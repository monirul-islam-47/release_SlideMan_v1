"""
Integration tests for keyword management workflow.
"""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from slideman.services.database import Database
from slideman.services.service_registry import ServiceRegistry
from slideman.presenters.keyword_manager_presenter import KeywordManagerPresenter
from slideman.commands.merge_keywords_cmd import MergeKeywordsCommand
from slideman.commands.manage_slide_keyword import ManageSlideKeywordCommand
from slideman.models import Project, File, Slide, Element, FileStatus


class TestKeywordWorkflow:
    """Integration tests for keyword management workflow."""

    @pytest.fixture
    def test_db(self):
        """Create in-memory test database."""
        db = Database(":memory:")
        db.initialize()
        yield db
        db.close()

    @pytest.fixture
    def sample_project_data(self, test_db):
        """Create sample project with slides and elements."""
        # Create project
        project = test_db.create_project("Keyword Test Project", "Testing keywords")
        
        # Create files
        file1 = test_db.create_file(
            project_id=project.id,
            name="presentation1.pptx",
            path="/path/pres1.pptx",
            size=1024,
            total_slides=3
        )
        
        file2 = test_db.create_file(
            project_id=project.id,
            name="presentation2.pptx",
            path="/path/pres2.pptx",
            size=2048,
            total_slides=2
        )
        
        # Create slides
        slides = []
        for file_obj, slide_count in [(file1, 3), (file2, 2)]:
            for i in range(slide_count):
                slide = test_db.create_slide(
                    file_id=file_obj.id,
                    slide_number=i + 1,
                    title=f"Slide {i + 1} from {file_obj.name}",
                    notes=f"Notes for slide {i + 1}",
                    thumbnail_path=f"/thumb/{file_obj.id}_{i + 1}.png"
                )
                slides.append(slide)
                
                # Create elements for each slide
                for j in range(2):
                    test_db.create_element(
                        slide_id=slide.id,
                        type="text" if j == 0 else "shape",
                        content=f"Element {j + 1} on slide {slide.id}"
                    )
        
        return {
            'project': project,
            'files': [file1, file2],
            'slides': slides
        }

    @pytest.fixture
    def service_registry(self, test_db):
        """Create service registry with test database."""
        registry = ServiceRegistry()
        registry.register('database', test_db)
        registry.register('thumbnail_cache', Mock())  # Mock thumbnail service
        return registry

    def test_keyword_creation_and_tagging(self, test_db, sample_project_data):
        """Test creating keywords and tagging slides."""
        project = sample_project_data['project']
        slides = sample_project_data['slides']
        
        # Create keywords
        keywords = []
        for name in ["important", "review", "draft", "final"]:
            keyword = test_db.create_keyword(name)
            keywords.append(keyword)
        
        # Tag slides
        test_db.add_slide_keyword(slides[0].id, keywords[0].id)  # important
        test_db.add_slide_keyword(slides[0].id, keywords[1].id)  # review
        test_db.add_slide_keyword(slides[1].id, keywords[0].id)  # important
        test_db.add_slide_keyword(slides[2].id, keywords[2].id)  # draft
        test_db.add_slide_keyword(slides[3].id, keywords[3].id)  # final
        test_db.add_slide_keyword(slides[4].id, keywords[3].id)  # final
        
        # Verify tagging
        slide0_keywords = test_db.get_slide_keywords(slides[0].id)
        assert len(slide0_keywords) == 2
        assert set(k.name for k in slide0_keywords) == {"important", "review"}
        
        # Test keyword usage counts
        assert test_db.get_keyword_usage_count(keywords[0].id) == 2  # important
        assert test_db.get_keyword_usage_count(keywords[3].id) == 2  # final
        assert test_db.get_keyword_usage_count(keywords[2].id) == 1  # draft

    def test_keyword_search_and_filter(self, test_db, sample_project_data):
        """Test searching and filtering by keywords."""
        project = sample_project_data['project']
        slides = sample_project_data['slides']
        
        # Setup keywords
        important = test_db.create_keyword("important")
        urgent = test_db.create_keyword("urgent")
        
        test_db.add_slide_keyword(slides[0].id, important.id)
        test_db.add_slide_keyword(slides[0].id, urgent.id)
        test_db.add_slide_keyword(slides[2].id, important.id)
        test_db.add_slide_keyword(slides[4].id, urgent.id)
        
        # Search slides with specific keyword
        important_slides = test_db.search_slides_by_keywords(project.id, [important.id])
        assert len(important_slides) == 2
        assert set(s.id for s in important_slides) == {slides[0].id, slides[2].id}
        
        # Search with multiple keywords (AND)
        both_keywords = test_db.search_slides_by_keywords(project.id, [important.id, urgent.id])
        assert len(both_keywords) == 1
        assert both_keywords[0].id == slides[0].id
        
        # Full-text search combined with keywords
        results = test_db.search_slides(project.id, "Slide 1", keyword_ids=[important.id])
        assert len(results) == 1
        assert results[0].id == slides[0].id

    def test_keyword_merge_workflow(self, test_db, sample_project_data):
        """Test merging duplicate keywords."""
        slides = sample_project_data['slides']
        
        # Create similar keywords (typos, variations)
        important = test_db.create_keyword("important")
        important_typo = test_db.create_keyword("imporant")  # typo
        critical = test_db.create_keyword("critical")
        
        # Tag slides with both variations
        test_db.add_slide_keyword(slides[0].id, important.id)
        test_db.add_slide_keyword(slides[1].id, important_typo.id)
        test_db.add_slide_keyword(slides[2].id, important.id)
        test_db.add_slide_keyword(slides[2].id, important_typo.id)
        test_db.add_slide_keyword(slides[3].id, critical.id)
        
        # Also tag some elements
        elements = test_db.get_slide_elements(slides[0].id)
        test_db.add_element_keyword(elements[0].id, important_typo.id)
        
        # Execute merge command
        merge_cmd = MergeKeywordsCommand("imporant", "important", test_db)
        merge_cmd.redo()
        
        # Verify merge results
        # Old keyword should be deleted
        assert test_db.get_keyword_by_name("imporant") is None
        
        # All items should now have the correct keyword
        slide1_keywords = [k.name for k in test_db.get_slide_keywords(slides[1].id)]
        assert "important" in slide1_keywords
        assert "imporant" not in slide1_keywords
        
        # Slide 2 should not have duplicates
        slide2_keywords = test_db.get_slide_keywords(slides[2].id)
        assert len(slide2_keywords) == 1
        assert slide2_keywords[0].name == "important"
        
        # Element should be updated
        element_keywords = test_db.get_element_keywords(elements[0].id)
        assert len(element_keywords) == 1
        assert element_keywords[0].name == "important"
        
        # Test undo
        merge_cmd.undo()
        
        # Old keyword should be restored
        restored = test_db.get_keyword_by_name("imporant")
        assert restored is not None
        
        # Original associations should be restored
        slide1_keywords_after_undo = [k.name for k in test_db.get_slide_keywords(slides[1].id)]
        assert "imporant" in slide1_keywords_after_undo

    def test_element_level_tagging(self, test_db, sample_project_data):
        """Test tagging individual slide elements."""
        slides = sample_project_data['slides']
        
        # Create keywords for elements
        chart_kw = test_db.create_keyword("chart")
        data_kw = test_db.create_keyword("data")
        graphic_kw = test_db.create_keyword("graphic")
        
        # Get elements from first slide
        elements = test_db.get_slide_elements(slides[0].id)
        assert len(elements) >= 2
        
        # Tag elements
        test_db.add_element_keyword(elements[0].id, chart_kw.id)
        test_db.add_element_keyword(elements[0].id, data_kw.id)
        test_db.add_element_keyword(elements[1].id, graphic_kw.id)
        
        # Verify element tags
        elem0_keywords = test_db.get_element_keywords(elements[0].id)
        assert len(elem0_keywords) == 2
        assert set(k.name for k in elem0_keywords) == {"chart", "data"}
        
        # Test element keyword removal
        test_db.remove_element_keyword(elements[0].id, data_kw.id)
        elem0_keywords_after = test_db.get_element_keywords(elements[0].id)
        assert len(elem0_keywords_after) == 1
        assert elem0_keywords_after[0].name == "chart"

    def test_keyword_presenter_integration(self, service_registry, sample_project_data):
        """Test KeywordManagerPresenter integration."""
        project = sample_project_data['project']
        
        # Create mock view
        view = Mock()
        view.get_selected_slide_id.return_value = sample_project_data['slides'][0].id
        view.get_slide_tag_edits.return_value = (["new_tag"], ["old_tag"])
        view.get_element_tag_edits.return_value = ["element_tag"]
        
        # Create presenter
        presenter = KeywordManagerPresenter(view, {
            'database': service_registry.get('database'),
            'thumbnail_cache': service_registry.get('thumbnail_cache')
        })
        
        # Load project data
        presenter.load_project_data(project.id)
        
        # Verify view updates
        view.update_keyword_table.assert_called()
        view.update_statistics.assert_called()
        
        # Test finding similar keywords
        db = service_registry.get('database')
        similar1 = db.create_keyword("presentation")
        similar2 = db.create_keyword("presentations")
        
        all_keywords = db.get_all_keywords()
        
        # Mock similarity detection
        with patch('slideman.services.keyword_tasks.KeywordSimilarityWorker'):
            presenter.find_similar_keywords(all_keywords)

    def test_bulk_keyword_operations(self, test_db, sample_project_data):
        """Test bulk keyword operations on multiple slides."""
        slides = sample_project_data['slides']
        
        # Create keywords
        batch_kw = test_db.create_keyword("batch_processed")
        review_kw = test_db.create_keyword("needs_review")
        
        # Bulk add keyword to multiple slides
        slide_ids = [s.id for s in slides[:3]]  # First 3 slides
        
        for slide_id in slide_ids:
            cmd = ManageSlideKeywordCommand(slide_id, batch_kw.id, is_add=True, db_service=test_db)
            cmd.redo()
        
        # Verify bulk operation
        for slide_id in slide_ids:
            keywords = test_db.get_slide_keywords(slide_id)
            assert any(k.id == batch_kw.id for k in keywords)
        
        # Bulk remove
        for slide_id in slide_ids[:2]:  # Remove from first 2
            cmd = ManageSlideKeywordCommand(slide_id, batch_kw.id, is_add=False, db_service=test_db)
            cmd.redo()
        
        # Verify removal
        assert not any(k.id == batch_kw.id for k in test_db.get_slide_keywords(slides[0].id))
        assert not any(k.id == batch_kw.id for k in test_db.get_slide_keywords(slides[1].id))
        assert any(k.id == batch_kw.id for k in test_db.get_slide_keywords(slides[2].id))

    def test_keyword_statistics_and_cleanup(self, test_db, sample_project_data):
        """Test keyword statistics and unused keyword cleanup."""
        project = sample_project_data['project']
        slides = sample_project_data['slides']
        
        # Create mix of used and unused keywords
        used_keywords = []
        for name in ["used1", "used2", "used3"]:
            kw = test_db.create_keyword(name)
            used_keywords.append(kw)
            # Tag at least one slide
            test_db.add_slide_keyword(slides[0].id, kw.id)
        
        unused_keywords = []
        for name in ["unused1", "unused2"]:
            kw = test_db.create_keyword(name)
            unused_keywords.append(kw)
        
        # Get statistics
        all_keywords = test_db.get_all_keywords()
        total_count = len(all_keywords)
        
        unused_count = sum(1 for kw in all_keywords if test_db.get_keyword_usage_count(kw.id) == 0)
        
        assert total_count == 5
        assert unused_count == 2
        
        # Identify and potentially clean up unused keywords
        for kw in all_keywords:
            usage = test_db.get_keyword_usage_count(kw.id)
            if usage == 0:
                # Could delete unused keywords
                assert kw.name in ["unused1", "unused2"]