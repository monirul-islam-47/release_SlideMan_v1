"""
Unit tests for FileIO service.
"""
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import hashlib

import pytest

from slideman.services.file_io import FileIO
from slideman.services.exceptions import FileOperationError, ValidationError


class TestFileIO:
    """Test suite for FileIO service."""

    @pytest.fixture
    def file_io(self):
        """Create FileIO instance."""
        return FileIO()

    @pytest.fixture
    def temp_project_dir(self, tmp_path):
        """Create a temporary project directory structure."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "sources").mkdir()
        (project_dir / "thumbnails").mkdir()
        return project_dir

    @pytest.fixture
    def sample_file(self, tmp_path):
        """Create a sample file for testing."""
        file_path = tmp_path / "sample.pptx"
        file_path.write_bytes(b"Sample PowerPoint content" * 100)
        return file_path

    def test_get_user_data_directory_windows(self, file_io):
        """Test getting user data directory on Windows."""
        with patch.dict(os.environ, {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'}):
            result = file_io.get_user_data_directory()
            assert result == Path('C:\\Users\\Test\\AppData\\Roaming\\SlideMan')

    def test_get_user_data_directory_unix(self, file_io):
        """Test getting user data directory on Unix systems."""
        with patch.dict(os.environ, {'HOME': '/home/test'}, clear=True):
            # Remove APPDATA to simulate Unix
            os.environ.pop('APPDATA', None)
            result = file_io.get_user_data_directory()
            assert result == Path('/home/test/.slideman')

    def test_get_projects_directory(self, file_io):
        """Test getting projects directory."""
        with patch.object(file_io, 'get_user_data_directory') as mock_get_dir:
            mock_get_dir.return_value = Path('/data/slideman')
            result = file_io.get_projects_directory()
            assert result == Path('/data/slideman/projects')

    def test_get_project_path(self, file_io):
        """Test getting specific project path."""
        with patch.object(file_io, 'get_projects_directory') as mock_get_dir:
            mock_get_dir.return_value = Path('/data/projects')
            result = file_io.get_project_path('test_project')
            assert result == Path('/data/projects/test_project')

    def test_create_project_structure_success(self, file_io, temp_project_dir):
        """Test successful project structure creation."""
        project_name = "new_project"
        project_path = temp_project_dir.parent / project_name
        
        with patch.object(file_io, 'get_project_path', return_value=project_path):
            result = file_io.create_project_structure(project_name)
        
        assert result == project_path
        assert project_path.exists()
        assert (project_path / "sources").exists()
        assert (project_path / "thumbnails").exists()

    def test_create_project_structure_already_exists(self, file_io, temp_project_dir):
        """Test creating project structure when it already exists."""
        with patch.object(file_io, 'get_project_path', return_value=temp_project_dir):
            with pytest.raises(ValidationError) as exc_info:
                file_io.create_project_structure("test_project")
            assert "already exists" in str(exc_info.value)

    def test_delete_project_structure_success(self, file_io, temp_project_dir):
        """Test successful project deletion."""
        with patch.object(file_io, 'get_project_path', return_value=temp_project_dir):
            file_io.delete_project_structure("test_project")
        
        assert not temp_project_dir.exists()

    def test_delete_project_structure_not_found(self, file_io, tmp_path):
        """Test deleting non-existent project."""
        non_existent = tmp_path / "non_existent"
        with patch.object(file_io, 'get_project_path', return_value=non_existent):
            # Should not raise error
            file_io.delete_project_structure("non_existent")

    def test_is_valid_powerpoint(self, file_io, tmp_path):
        """Test PowerPoint file validation."""
        # Valid extensions
        valid_files = [
            tmp_path / "presentation.pptx",
            tmp_path / "old_format.ppt",
            tmp_path / "UPPERCASE.PPTX"
        ]
        
        for file in valid_files:
            file.touch()
            assert file_io.is_valid_powerpoint(file) is True
        
        # Invalid extensions
        invalid_files = [
            tmp_path / "document.docx",
            tmp_path / "spreadsheet.xlsx",
            tmp_path / "text.txt"
        ]
        
        for file in invalid_files:
            file.touch()
            assert file_io.is_valid_powerpoint(file) is False

    def test_get_file_size(self, file_io, sample_file):
        """Test getting file size."""
        size = file_io.get_file_size(sample_file)
        assert size == 2500  # 25 * 100 bytes

    def test_get_file_size_not_found(self, file_io, tmp_path):
        """Test getting size of non-existent file."""
        non_existent = tmp_path / "missing.pptx"
        size = file_io.get_file_size(non_existent)
        assert size == 0

    def test_copy_file_to_project_success(self, file_io, temp_project_dir, sample_file):
        """Test successful file copy to project."""
        dest = file_io.copy_file_to_project(sample_file, temp_project_dir)
        
        assert dest == temp_project_dir / "sources" / "sample.pptx"
        assert dest.exists()
        assert dest.read_bytes() == sample_file.read_bytes()

    def test_copy_file_to_project_duplicate_handling(self, file_io, temp_project_dir, sample_file):
        """Test copying file with duplicate name."""
        # Copy first time
        first_copy = file_io.copy_file_to_project(sample_file, temp_project_dir)
        
        # Copy second time - should add suffix
        second_copy = file_io.copy_file_to_project(sample_file, temp_project_dir)
        
        assert first_copy.name == "sample.pptx"
        assert second_copy.name == "sample_1.pptx"
        assert second_copy.exists()

    def test_copy_file_to_project_permission_error(self, file_io, temp_project_dir, sample_file):
        """Test file copy with permission error."""
        with patch('shutil.copy2', side_effect=PermissionError("Access denied")):
            with pytest.raises(FileOperationError) as exc_info:
                file_io.copy_file_to_project(sample_file, temp_project_dir)
            assert "Failed to copy file" in str(exc_info.value)

    def test_check_disk_space_sufficient(self, file_io):
        """Test disk space check with sufficient space."""
        with patch('shutil.disk_usage') as mock_usage:
            mock_usage.return_value = Mock(free=10 * 1024 * 1024 * 1024)  # 10 GB
            
            result = file_io.check_disk_space(Path("/test"), 1024 * 1024 * 1024)  # 1 GB
            assert result is True

    def test_check_disk_space_insufficient(self, file_io):
        """Test disk space check with insufficient space."""
        with patch('shutil.disk_usage') as mock_usage:
            mock_usage.return_value = Mock(free=500 * 1024 * 1024)  # 500 MB
            
            result = file_io.check_disk_space(Path("/test"), 1024 * 1024 * 1024)  # 1 GB
            assert result is False

    def test_calculate_checksum(self, file_io, sample_file):
        """Test file checksum calculation."""
        checksum = file_io.calculate_checksum(sample_file)
        
        # Verify it's a valid SHA-256 hash
        assert len(checksum) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)
        
        # Verify consistency
        checksum2 = file_io.calculate_checksum(sample_file)
        assert checksum == checksum2

    def test_calculate_checksum_large_file(self, file_io, tmp_path):
        """Test checksum calculation for large file."""
        large_file = tmp_path / "large.pptx"
        # Create 10MB file
        with open(large_file, 'wb') as f:
            for _ in range(10):
                f.write(b'x' * (1024 * 1024))
        
        checksum = file_io.calculate_checksum(large_file)
        assert len(checksum) == 64

    def test_calculate_checksum_not_found(self, file_io, tmp_path):
        """Test checksum calculation for missing file."""
        non_existent = tmp_path / "missing.pptx"
        
        with pytest.raises(FileOperationError) as exc_info:
            file_io.calculate_checksum(non_existent)
        assert "not found" in str(exc_info.value)

    def test_get_unique_filename(self, file_io, temp_project_dir):
        """Test generating unique filenames."""
        sources_dir = temp_project_dir / "sources"
        
        # First file
        name1 = file_io._get_unique_filename(sources_dir, "test.pptx")
        assert name1 == "test.pptx"
        
        # Create the file
        (sources_dir / name1).touch()
        
        # Second file with same name
        name2 = file_io._get_unique_filename(sources_dir, "test.pptx")
        assert name2 == "test_1.pptx"
        
        # Create second file
        (sources_dir / name2).touch()
        
        # Third file
        name3 = file_io._get_unique_filename(sources_dir, "test.pptx")
        assert name3 == "test_2.pptx"

    def test_copy_files_to_project_batch(self, file_io, temp_project_dir, tmp_path):
        """Test copying multiple files to project."""
        # Create test files
        files = []
        for i in range(3):
            file = tmp_path / f"presentation{i}.pptx"
            file.write_text(f"Content {i}")
            files.append(file)
        
        results = file_io.copy_files_to_project(files, temp_project_dir)
        
        assert len(results) == 3
        for i, dest in enumerate(results):
            assert dest.name == f"presentation{i}.pptx"
            assert dest.read_text() == f"Content {i}"

    def test_copy_files_to_project_mixed_success(self, file_io, temp_project_dir, tmp_path):
        """Test copying files with some failures."""
        valid_file = tmp_path / "valid.pptx"
        valid_file.touch()
        
        invalid_file = tmp_path / "invalid.docx"
        invalid_file.touch()
        
        results = file_io.copy_files_to_project([valid_file, invalid_file], temp_project_dir)
        
        # Should only copy valid PowerPoint file
        assert len(results) == 1
        assert results[0].name == "valid.pptx"

    def test_get_thumbnail_path(self, file_io, temp_project_dir):
        """Test getting thumbnail path for slide."""
        path = file_io.get_thumbnail_path(temp_project_dir, 1, 5)
        expected = temp_project_dir / "thumbnails" / "file_1_slide_5.png"
        assert path == expected

    def test_ensure_directory_exists(self, file_io, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "new" / "nested" / "directory"
        
        file_io._ensure_directory_exists(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_safe_path_join(self, file_io):
        """Test safe path joining."""
        # Normal case
        result = file_io._safe_path_join(Path("/base"), "subdir", "file.txt")
        assert result == Path("/base/subdir/file.txt")
        
        # With Path objects
        result = file_io._safe_path_join(Path("/base"), Path("subdir"), "file.txt")
        assert result == Path("/base/subdir/file.txt")