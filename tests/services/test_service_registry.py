"""
Unit tests for ServiceRegistry.
"""
from unittest.mock import Mock

import pytest

from slideman.services.service_registry import ServiceRegistry


class TestServiceRegistry:
    """Test suite for ServiceRegistry."""

    @pytest.fixture
    def registry(self):
        """Create ServiceRegistry instance."""
        return ServiceRegistry()

    def test_initialization(self, registry):
        """Test registry initialization."""
        assert registry._services == {}

    def test_register_service(self, registry):
        """Test registering a service."""
        mock_service = Mock()
        
        registry.register('test_service', mock_service)
        
        assert 'test_service' in registry._services
        assert registry._services['test_service'] == mock_service

    def test_register_duplicate_service(self, registry):
        """Test registering duplicate service overwrites."""
        service1 = Mock()
        service2 = Mock()
        
        registry.register('test_service', service1)
        registry.register('test_service', service2)
        
        assert registry._services['test_service'] == service2

    def test_get_existing_service(self, registry):
        """Test getting registered service."""
        mock_service = Mock()
        registry.register('test_service', mock_service)
        
        result = registry.get('test_service')
        
        assert result == mock_service

    def test_get_nonexistent_service(self, registry):
        """Test getting non-existent service returns None."""
        result = registry.get('nonexistent')
        
        assert result is None

    def test_get_all_services(self, registry):
        """Test getting all registered services."""
        service1 = Mock()
        service2 = Mock()
        service3 = Mock()
        
        registry.register('service1', service1)
        registry.register('service2', service2)
        registry.register('service3', service3)
        
        all_services = registry.get_all()
        
        assert len(all_services) == 3
        assert all_services['service1'] == service1
        assert all_services['service2'] == service2
        assert all_services['service3'] == service3

    def test_has_service(self, registry):
        """Test checking if service exists."""
        mock_service = Mock()
        registry.register('test_service', mock_service)
        
        assert registry.has('test_service') is True
        assert registry.has('nonexistent') is False

    def test_unregister_service(self, registry):
        """Test unregistering a service."""
        mock_service = Mock()
        registry.register('test_service', mock_service)
        
        registry.unregister('test_service')
        
        assert 'test_service' not in registry._services
        assert registry.get('test_service') is None

    def test_unregister_nonexistent_service(self, registry):
        """Test unregistering non-existent service doesn't raise error."""
        # Should not raise exception
        registry.unregister('nonexistent')

    def test_clear_all_services(self, registry):
        """Test clearing all services."""
        registry.register('service1', Mock())
        registry.register('service2', Mock())
        registry.register('service3', Mock())
        
        registry.clear()
        
        assert len(registry._services) == 0
        assert registry.get_all() == {}

    def test_service_names(self, registry):
        """Test getting list of service names."""
        registry.register('service1', Mock())
        registry.register('service2', Mock())
        registry.register('service3', Mock())
        
        names = registry.get_service_names()
        
        assert len(names) == 3
        assert 'service1' in names
        assert 'service2' in names
        assert 'service3' in names

    def test_register_with_none_value(self, registry):
        """Test registering None as service value."""
        registry.register('null_service', None)
        
        assert registry.has('null_service') is True
        assert registry.get('null_service') is None

    def test_lazy_initialization_pattern(self, registry):
        """Test lazy initialization pattern with factory function."""
        initialization_count = 0
        
        def create_service():
            nonlocal initialization_count
            initialization_count += 1
            return Mock()
        
        # Register factory
        registry.register('lazy_service', create_service)
        
        # Service not created yet
        assert initialization_count == 0
        
        # Get service (would trigger creation in lazy pattern)
        # Note: Current implementation stores the factory, not the result
        factory = registry.get('lazy_service')
        assert callable(factory)
        
        # Call factory to create service
        service = factory()
        assert initialization_count == 1

    def test_service_replacement_notification(self, registry):
        """Test that service replacement can be detected."""
        original = Mock()
        replacement = Mock()
        
        registry.register('service', original)
        original_ref = registry.get('service')
        
        registry.register('service', replacement)
        new_ref = registry.get('service')
        
        assert original_ref != new_ref
        assert new_ref == replacement

    def test_thread_safety_simulation(self, registry):
        """Test basic thread safety of registry operations."""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        results = []
        lock = threading.Lock()
        
        def register_service(name, value):
            registry.register(name, value)
            with lock:
                results.append((name, value))
        
        # Multiple threads registering services
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(10):
                future = executor.submit(register_service, f'service_{i}', i)
                futures.append(future)
            
            # Wait for all to complete
            for future in futures:
                future.result()
        
        # Verify all services registered
        assert len(results) == 10
        for i in range(10):
            assert registry.has(f'service_{i}')
            assert registry.get(f'service_{i}') == i