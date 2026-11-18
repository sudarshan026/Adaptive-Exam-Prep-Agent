"""Syllabus upload, parsing, subject/topic management endpoints."""
import os
import json
import logging
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

def _basic_syllabus_parse(text: str) -> dict:
    """Robust heuristic parsing for syllabus text extracting real subjects and topics."""
    import re
    subjects = []
    current_subject = None
    
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    for line in lines:
        if len(line) <= 2 or line.isdigit():
            continue
            
        # Subject detection heuristics
        subject_match = re.match(r'^(Subject|Course|Paper\s*\d*|Section\s*[A-Z]|Part\s*[IVX]+)\s*[:.-]\s*(.+)', line, re.I)
        if subject_match:
            current_subject = {"name": subject_match.group(2).strip().title(), "topics": []}
            subjects.append(current_subject)
            continue
        elif (line.isupper() and 3 < len(line) < 60 and not any(c.isdigit() for c in line) and not line.startswith(('PAGE', 'TOTAL', 'MARKS', 'HOURS', 'SEMESTER'))):
            current_subject = {"name": line.title(), "topics": []}
            subjects.append(current_subject)
            continue
            
        # Topic detection heuristics
        is_topic_line = (
            re.match(r'^(Module|Unit|Chapter|Topic)\s+\d+[:.-]*\s*(.+)', line, re.I) or
            re.match(r'^[IVXLCDM]+\.[:.-]*\s*(.+)', line) or
            re.match(r'^\d+(\.\d+)?[:.)-]\s*(.+)', line) or
            re.match(r'^[-*•]\s*(.+)', line)
        )
        
        if is_topic_line:
            topic_name = is_topic_line.group(len(is_topic_line.groups())).strip()
            if 3 <= len(topic_name) <= 120:
                if not current_subject:
                    current_subject = {"name": "Core Curriculum", "topics": []}
                    subjects.append(current_subject)
                current_subject["topics"].append({
                    "name": topic_name,
                    "difficulty": "medium",
                    "estimated_hours": 2.0
                })
        elif current_subject and 5 <= len(line) <= 80 and not line.endswith(':'):
            if len(current_subject["topics"]) < 10 and not any(line.lower().startswith(x) for x in ['page', 'credits', 'prerequisite', 'reference', 'textbook']):
                current_subject["topics"].append({
                    "name": line,
                    "difficulty": "medium",
                    "estimated_hours": 2.0
                })
                
    # Filter subjects that ended up with 0 topics if other populated subjects exist
    populated = [s for s in subjects if s.get("topics")]
    if populated:
        subjects = populated

    # If still no subjects/topics found, extract non-trivial lines
    if not subjects or not any(s.get("topics") for s in subjects):
        extracted_topics = [
            {"name": line[:100], "difficulty": "medium", "estimated_hours": 2.0}
            for line in lines
            if 10 < len(line) < 100 and not any(w in line.lower() for w in ['copyright', 'http', 'page', 'author', 'university', 'syllabus'])
        ][:12]
        subjects = [{
            "name": "Course Curriculum",
            "topics": extracted_topics if extracted_topics else [{"name": "Core Concepts & Fundamentals", "difficulty": "medium", "estimated_hours": 2.0}]
        }]
        
    return {"subjects": subjects}

from app.database.base import get_db
from app.models.syllabus import UploadedSyllabus, Subject, Topic, TopicDependency, LearningResource
from app.schemas.syllabus import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    TopicCreate, TopicUpdate, TopicResponse,
    DependencyCreate, DependencyResponse,
    ResourceCreate, ResourceResponse,
    SyllabusUploadResponse,
)
from app.core.security import get_current_user_id
from app.core.config import settings

router = APIRouter(prefix="/api/syllabus", tags=["Syllabus & Topics"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=SyllabusUploadResponse)
async def upload_syllabus(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a syllabus PDF for parsing."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Save file
    safe_name = f"{user_id}_{int(datetime.now(timezone.utc).timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Extract text with PyMuPDF
    extracted_text = ""
    try:
        import fitz
        doc = fitz.open(file_path)
        for page in doc:
            extracted_text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        extracted_text = f"PDF extraction failed: {str(e)}"
    
    # RAG Semantic Chunking & Indexing
    if extracted_text and "failed" not in extracted_text.lower():
        try:
            from app.services.rag_service import rag_index
            rag_index.chunk_document(
                text=extracted_text,
                source_document=file.filename,
                user_id=user_id,
            )
            logger.info(f"RAG: Document {file.filename} chunked and indexed successfully.")
        except Exception as e:
            logger.warning(f"RAG indexing warning: {e}")

    # Parse with LangGraph agent or fallback
    parsed_structure = None
    if not settings.is_demo_mode and extracted_text and "failed" not in extracted_text.lower():
        try:
            from app.agents import invoke_agent
            result = await invoke_agent(
                task="manage_syllabus",
                user_id=user_id,
                db=db,
                input_data={"raw_text": extracted_text, "exam_type": "Exam"}
            )
            parsed_structure = result.get("parsed_syllabus")
        except Exception as e:
            logger.warning(f"AI syllabus parsing failed: {e}")

    
    # If no AI parsing, try basic text-based extraction
    if not parsed_structure and extracted_text and "failed" not in extracted_text.lower():
        parsed_structure = _basic_syllabus_parse(extracted_text)
    
    # Last resort: inform user to add manually
    if not parsed_structure:
        parsed_structure = {"raw_text": extracted_text[:5000] if extracted_text else "", 
                          "note": "Could not parse syllabus automatically. Please add subjects and topics manually."}
    
    syllabus = UploadedSyllabus(
        user_id=user_id,
        filename=file.filename,
        file_path=file_path,
        extracted_text=extracted_text[:10000] if extracted_text else None,
        parsed_structure=parsed_structure,
        status="parsed" if parsed_structure.get("subjects") else "uploaded",
    )
    db.add(syllabus)
    await db.flush()
    return SyllabusUploadResponse.model_validate(syllabus)


@router.get("/uploads", response_model=list[SyllabusUploadResponse])
async def get_uploads(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all syllabus uploads for the current user."""
    result = await db.execute(
        select(UploadedSyllabus).where(UploadedSyllabus.user_id == user_id).order_by(UploadedSyllabus.created_at.desc())
    )
    return [SyllabusUploadResponse.model_validate(s) for s in result.scalars().all()]


# --- Subjects ---
@router.post("/subjects", response_model=SubjectResponse, status_code=201)
async def create_subject(
    data: SubjectCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    subject = Subject(user_id=user_id, **data.model_dump())
    db.add(subject)
    await db.flush()
    return SubjectResponse.model_validate(subject)


@router.get("/subjects", response_model=list[SubjectResponse])
async def get_subjects(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subject).where(Subject.user_id == user_id).order_by(Subject.order_index)
    )
    subjects = result.scalars().all()
    response = []
    for s in subjects:
        topic_result = await db.execute(
            select(Topic).where(Topic.subject_id == s.id).order_by(Topic.order_index)
        )
        topics = [TopicResponse.model_validate(t) for t in topic_result.scalars().all()]
        sr = SubjectResponse.model_validate(s)
        sr.topics = topics
        response.append(sr)
    return response


@router.put("/subjects/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(subject, key, value)
    await db.flush()
    return SubjectResponse.model_validate(subject)


@router.delete("/subjects/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subject).where(Subject.id == subject_id, Subject.user_id == user_id)
    )
    subject = result.scalar_one_or_none()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    await db.delete(subject)


# --- Topics ---
@router.post("/topics", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    # Verify subject belongs to user
    result = await db.execute(
        select(Subject).where(Subject.id == data.subject_id, Subject.user_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Subject not found")
    
    topic = Topic(user_id=user_id, **data.model_dump())
    db.add(topic)
    await db.flush()
    return TopicResponse.model_validate(topic)


@router.get("/topics", response_model=list[TopicResponse])
async def get_topics(
    subject_id: int = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(Topic).where(Topic.user_id == user_id)
    if subject_id:
        query = query.where(Topic.subject_id == subject_id)
    query = query.order_by(Topic.order_index)
    result = await db.execute(query)
    return [TopicResponse.model_validate(t) for t in result.scalars().all()]


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    data: TopicUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, key, value)
    await db.flush()
    return TopicResponse.model_validate(topic)


@router.delete("/topics/{topic_id}", status_code=204)
async def delete_topic(
    topic_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id)
    )
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    await db.delete(topic)


# --- Dependencies ---
@router.post("/dependencies", response_model=DependencyResponse, status_code=201)
async def create_dependency(
    data: DependencyCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    dep = TopicDependency(**data.model_dump())
    db.add(dep)
    await db.flush()
    return DependencyResponse.model_validate(dep)


@router.get("/dependencies", response_model=list[DependencyResponse])
async def get_dependencies(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    topics = await db.execute(select(Topic.id).where(Topic.user_id == user_id))
    topic_ids = [t[0] for t in topics.all()]
    if not topic_ids:
        return []
    result = await db.execute(
        select(TopicDependency).where(TopicDependency.topic_id.in_(topic_ids))
    )
    return [DependencyResponse.model_validate(d) for d in result.scalars().all()]


# --- Resources ---
@router.post("/resources", response_model=ResourceResponse, status_code=201)
async def create_resource(
    data: ResourceCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    resource = LearningResource(user_id=user_id, **data.model_dump())
    db.add(resource)
    await db.flush()
    return ResourceResponse.model_validate(resource)


@router.get("/resources", response_model=list[ResourceResponse])
async def get_resources(
    topic_id: int = None,
    saved_only: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    query = select(LearningResource).where(LearningResource.user_id == user_id)
    if topic_id:
        query = query.where(LearningResource.topic_id == topic_id)
    if saved_only:
        query = query.where(LearningResource.is_saved == 1)
    result = await db.execute(query.order_by(LearningResource.created_at.desc()))
    return [ResourceResponse.model_validate(r) for r in result.scalars().all()]


@router.put("/resources/{resource_id}/save", response_model=ResourceResponse)
async def toggle_save_resource(
    resource_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(LearningResource).where(LearningResource.id == resource_id, LearningResource.user_id == user_id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    resource.is_saved = 0 if resource.is_saved else 1
    await db.flush()
    return ResourceResponse.model_validate(resource)
