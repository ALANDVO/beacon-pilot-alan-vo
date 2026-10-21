"""Backend tests for memory CRUD operations."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Fixtures are defined in conftest.py


class TestHealthCheck:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["environment"] == "test"


class TestMemoryCRUD:
    """Test memory unit CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_memory(self, client):
        response = await client.post(
            "/memories",
            json={
                "document_id": "doc-1",
                "content": "User prefers dark mode",
                "tags": ["preference", "ui"],
                "metadata": {"source": "chat"},
                "observation_scopes": ["session-1"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "doc-1"
        assert data["content"] == "User prefers dark mode"
        assert data["tags"] == ["preference", "ui"]
        assert data["metadata"] == {"source": "chat"}
        assert data["observation_scopes"] == ["session-1"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert data["is_consolidated"] is False
    
    @pytest.mark.asyncio
    async def test_create_duplicate_memory_fails(self, client):
        """Creating a memory with same document_id and content_hash should fail."""
        payload = {
            "document_id": "doc-dup",
            "content": "Duplicate fact",
            "tags": ["test"],
            "metadata": {},
            "observation_scopes": [],
        }
        response1 = await client.post("/memories", json=payload)
        assert response1.status_code == 201
        
        response2 = await client.post("/memories", json=payload)
        assert response2.status_code == 409
    
    @pytest.mark.asyncio
    async def test_list_memories(self, client):
        # Create a few memories
        for i in range(3):
            await client.post("/memories", json={
                "document_id": f"doc-list-{i}",
                "content": f"Fact {i}",
                "tags": ["list-test"],
                "metadata": {},
                "observation_scopes": [],
            })
        
        response = await client.get("/memories")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] >= 1
    
    @pytest.mark.asyncio
    async def test_list_memories_with_filters(self, client):
        await client.post("/memories", json={
            "document_id": "doc-filter-1",
            "content": "Filter test alpha",
            "tags": ["alpha", "filter"],
            "metadata": {},
            "observation_scopes": [],
        })
        await client.post("/memories", json={
            "document_id": "doc-filter-2",
            "content": "Filter test beta",
            "tags": ["beta", "filter"],
            "metadata": {},
            "observation_scopes": [],
        })
        
        # Filter by tag
        response = await client.get("/memories?tag=alpha")
        assert response.status_code == 200
        data = response.json()
        assert all("alpha" in item["tags"] for item in data["items"])
        
        # Filter by document_id
        response = await client.get("/memories?document_id=doc-filter-1")
        assert response.status_code == 200
        data = response.json()
        assert all(item["document_id"] == "doc-filter-1" for item in data["items"])
        
        # Filter by search
        response = await client.get("/memories?search=alpha")
        assert response.status_code == 200
        data = response.json()
        assert all("alpha" in item["content"].lower() for item in data["items"])
    
    @pytest.mark.asyncio
    async def test_get_memory(self, client):
        create_response = await client.post("/memories", json={
            "document_id": "doc-get",
            "content": "Get this memory",
            "tags": ["get-test"],
            "metadata": {},
            "observation_scopes": [],
        })
        assert create_response.status_code == 201
        memory_id = create_response.json()["id"]
        
        response = await client.get(f"/memories/{memory_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memory_id
        assert data["content"] == "Get this memory"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, client):
        response = await client.get("/memories/999999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_memory(self, client):
        create_response = await client.post("/memories", json={
            "document_id": "doc-update",
            "content": "Original content",
            "tags": ["original"],
            "metadata": {},
            "observation_scopes": [],
        })
        assert create_response.status_code == 201
        memory_id = create_response.json()["id"]
        
        response = await client.patch(f"/memories/{memory_id}", json={
            "content": "Updated content",
            "tags": ["updated"],
        })
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["tags"] == ["updated"]
        assert data["id"] == memory_id
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_memory(self, client):
        response = await client.patch("/memories/999999", json={
            "content": "Won't work",
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, client):
        create_response = await client.post("/memories", json={
            "document_id": "doc-delete",
            "content": "To be deleted",
            "tags": ["delete-test"],
            "metadata": {},
            "observation_scopes": [],
        })
        assert create_response.status_code == 201
        memory_id = create_response.json()["id"]
        
        response = await client.delete(f"/memories/{memory_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = await client.get(f"/memories/{memory_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, client):
        response = await client.delete("/memories/999999")
        assert response.status_code == 404


class TestPagination:
    """Test pagination behavior."""
    
    @pytest.mark.asyncio
    async def test_pagination_page_size(self, client):
        # Create 15 memories
        for i in range(15):
            await client.post("/memories", json={
                "document_id": f"doc-page-{i}",
                "content": f"Pagination fact {i}",
                "tags": ["pagination"],
                "metadata": {},
                "observation_scopes": [],
            })
        
        response = await client.get("/memories?page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page_size"] == 5
        assert data["total"] >= 15
    
    @pytest.mark.asyncio
    async def test_pagination_second_page(self, client):
        response = await client.get("/memories?page=2&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["items"]) == 5


class TestAuditLog:
    """Test audit logging."""
    
    @pytest.mark.asyncio
    async def test_audit_log_on_create(self, client, test_session):
        from app.models.memory import AuditLog
        from sqlalchemy import select
        
        response = await client.post("/memories", json={
            "document_id": "doc-audit-create",
            "content": "Audit create test",
            "tags": ["audit"],
            "metadata": {},
            "observation_scopes": [],
        })
        assert response.status_code == 201
        
        result = await test_session.execute(
            select(AuditLog).where(AuditLog.action == "create")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].action == "create"
        assert logs[-1].resource_type == "memory_unit"
    
    @pytest.mark.asyncio
    async def test_audit_log_on_update(self, client, test_session):
        from app.models.memory import AuditLog
        from sqlalchemy import select
        
        create_response = await client.post("/memories", json={
            "document_id": "doc-audit-update",
            "content": "Audit update test",
            "tags": ["audit"],
            "metadata": {},
            "observation_scopes": [],
        })
        memory_id = create_response.json()["id"]
        
        await client.patch(f"/memories/{memory_id}", json={
            "content": "Updated for audit",
        })
        
        result = await test_session.execute(
            select(AuditLog).where(AuditLog.action == "update")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].action == "update"
    
    @pytest.mark.asyncio
    async def test_audit_log_on_delete(self, client, test_session):
        from app.models.memory import AuditLog
        from sqlalchemy import select
        
        create_response = await client.post("/memories", json={
            "document_id": "doc-audit-delete",
            "content": "Audit delete test",
            "tags": ["audit"],
            "metadata": {},
            "observation_scopes": [],
        })
        memory_id = create_response.json()["id"]
        
        await client.delete(f"/memories/{memory_id}")
        
        result = await test_session.execute(
            select(AuditLog).where(AuditLog.action == "delete")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].action == "delete"


class TestConsolidation:
    """Test consolidation endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_consolidation_batch(self, client):
        response = await client.post("/consolidate", json={
            "document_id": "doc-consolidate-1",
            "metadata": {"source": "test"},
        })
        assert response.status_code == 202
        data = response.json()
        assert data["document_id"] == "doc-consolidate-1"
        assert data["status"] == "pending"
        assert "id" in data
    
    @pytest.mark.asyncio
    async def test_create_batch_nonexistent_document(self, client):
        response = await client.post("/consolidate", json={
            "document_id": "nonexistent-doc",
            "metadata": {},
        })
        # Should still create batch even if document has no memories
        assert response.status_code == 202
    
    @pytest.mark.asyncio
    async def test_get_consolidation_batch(self, client):
        create_response = await client.post("/consolidate", json={
            "document_id": "doc-get-batch",
            "metadata": {},
        })
        batch_id = create_response.json()["id"]
        
        response = await client.get(f"/consolidate/{batch_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == batch_id
        assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_run_consolidation(self, client):
        # Create some memories to consolidate
        for i in range(3):
            await client.post("/memories", json={
                "document_id": "doc-consolidate-run",
                "content": f"Consolidation fact {i}",
                "tags": ["consolidate"],
                "metadata": {},
                "observation_scopes": [],
            })
        
        create_response = await client.post("/consolidate", json={
            "document_id": "doc-consolidate-run",
            "metadata": {},
        })
        batch_id = create_response.json()["id"]
        
        response = await client.post(f"/consolidate/{batch_id}/run")
        assert response.status_code == 200
        data = response.json()
        assert "processed" in data
        assert "merged" in data
        assert "duration_ms" in data