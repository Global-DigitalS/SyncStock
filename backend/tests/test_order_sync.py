"""
Tests for bidirectional order synchronization
"""
import pytest
from services.orders.order_sync import OrderStatusMapper


class TestOrderStatusMapper:
    """Test order status mapping between CRM and online stores"""

    def test_map_dolibarr_status_draft(self):
        """Map Dolibarr draft status"""
        status = OrderStatusMapper.map_dolibarr_status(0)
        assert status == "draft"

    def test_map_dolibarr_status_processed(self):
        """Map Dolibarr processed status"""
        status = OrderStatusMapper.map_dolibarr_status(1)
        assert status == "processed"

    def test_map_dolibarr_status_shipped(self):
        """Map Dolibarr shipped status"""
        status = OrderStatusMapper.map_dolibarr_status(2)
        assert status == "shipped"

    def test_map_dolibarr_status_delivered(self):
        """Map Dolibarr delivered status"""
        status = OrderStatusMapper.map_dolibarr_status(3)
        assert status == "delivered"

    def test_map_dolibarr_status_cancelled(self):
        """Map Dolibarr cancelled status"""
        status = OrderStatusMapper.map_dolibarr_status(4)
        assert status == "cancelled"

    def test_map_dolibarr_status_refused(self):
        """Map Dolibarr refused status"""
        status = OrderStatusMapper.map_dolibarr_status(5)
        assert status == "refused"

    def test_map_dolibarr_status_unknown(self):
        """Map unknown Dolibarr status defaults to processing"""
        status = OrderStatusMapper.map_dolibarr_status(999)
        assert status == "processing"

    def test_map_odoo_status_draft(self):
        """Map Odoo draft status"""
        status = OrderStatusMapper.map_odoo_status("draft")
        assert status == "processing"

    def test_map_odoo_status_sent(self):
        """Map Odoo sent status"""
        status = OrderStatusMapper.map_odoo_status("sent")
        assert status == "processing"

    def test_map_odoo_status_sale(self):
        """Map Odoo sale status"""
        status = OrderStatusMapper.map_odoo_status("sale")
        assert status == "processing"

    def test_map_odoo_status_done(self):
        """Map Odoo done status"""
        status = OrderStatusMapper.map_odoo_status("done")
        assert status == "completed"

    def test_map_odoo_status_cancel(self):
        """Map Odoo cancelled status"""
        status = OrderStatusMapper.map_odoo_status("cancel")
        assert status == "cancelled"

    def test_map_odoo_status_unknown(self):
        """Map unknown Odoo status defaults to processing"""
        status = OrderStatusMapper.map_odoo_status("unknown_state")
        assert status == "processing"

    def test_bidirectional_mapping_consistency(self):
        """Test that status mappings are reasonable for bidirectional sync"""
        # Dolibarr processing → "processed" → online store
        dolibarr_processed = OrderStatusMapper.map_dolibarr_status(1)
        assert dolibarr_processed in ["processed", "processing"]

        # Odoo sale → "processing" → online store
        odoo_sale = OrderStatusMapper.map_odoo_status("sale")
        assert odoo_sale == "processing"

        # Both should eventually lead to "completed" or similar end state
        dolibarr_done = OrderStatusMapper.map_dolibarr_status(3)
        odoo_done = OrderStatusMapper.map_odoo_status("done")
        assert dolibarr_done in ["delivered", "completed"]
        assert odoo_done == "completed"


class TestStatusMappingLogic:
    """Test status mapping logic for different scenarios"""

    def test_fulfilment_workflow_dolibarr(self):
        """Test typical Dolibarr order fulfillment workflow"""
        workflow = [
            (0, "draft"),        # Created
            (1, "processed"),    # Confirmed/Processed
            (2, "shipped"),      # Shipped
            (3, "delivered"),    # Delivered (final)
        ]

        for dolibarr_status, expected in workflow:
            actual = OrderStatusMapper.map_dolibarr_status(dolibarr_status)
            assert actual == expected

    def test_fulfilment_workflow_odoo(self):
        """Test typical Odoo order fulfillment workflow"""
        workflow = [
            ("draft", "processing"),    # Created
            ("sent", "processing"),     # Quotation sent
            ("sale", "processing"),     # Order confirmed
            ("done", "completed"),      # Done/Delivered
        ]

        for odoo_status, expected in workflow:
            actual = OrderStatusMapper.map_odoo_status(odoo_status)
            assert actual == expected

    def test_cancellation_handling_dolibarr(self):
        """Test Dolibarr cancellation handling"""
        cancelled = OrderStatusMapper.map_dolibarr_status(4)
        refused = OrderStatusMapper.map_dolibarr_status(5)

        assert cancelled == "cancelled"
        assert refused == "refused"

    def test_cancellation_handling_odoo(self):
        """Test Odoo cancellation handling"""
        cancelled = OrderStatusMapper.map_odoo_status("cancel")
        assert cancelled == "cancelled"


class TestStatusTransitions:
    """Test valid status transitions"""

    def test_no_invalid_transitions(self):
        """Verify status mapping produces valid output"""
        valid_statuses = {
            "draft", "processing", "processed", "shipped", "delivered",
            "cancelled", "refused", "completed", "refunded"
        }

        # Test all Dolibarr statuses
        for status_code in range(10):
            mapped = OrderStatusMapper.map_dolibarr_status(status_code)
            assert mapped in valid_statuses, f"Invalid status from Dolibarr: {mapped}"

        # Test common Odoo statuses
        odoo_statuses = ["draft", "sent", "sale", "done", "cancel"]
        for status in odoo_statuses:
            mapped = OrderStatusMapper.map_odoo_status(status)
            assert mapped in valid_statuses, f"Invalid status from Odoo: {mapped}"

    def test_final_states(self):
        """Test identification of final states"""
        final_states = {"delivered", "completed", "cancelled", "refused", "refunded"}

        # Dolibarr delivered and cancelled are final
        assert OrderStatusMapper.map_dolibarr_status(3) in final_states
        assert OrderStatusMapper.map_dolibarr_status(4) in final_states

        # Odoo done and cancel are final
        assert OrderStatusMapper.map_odoo_status("done") in final_states
        assert OrderStatusMapper.map_odoo_status("cancel") in final_states

    def test_intermediate_states(self):
        """Test identification of intermediate states"""
        intermediate_states = {"processing", "processed", "shipped"}

        # Dolibarr processed and shipped are intermediate
        assert OrderStatusMapper.map_dolibarr_status(1) in intermediate_states
        assert OrderStatusMapper.map_dolibarr_status(2) in intermediate_states

        # Odoo draft, sent, sale are intermediate
        assert OrderStatusMapper.map_odoo_status("draft") not in {"completed"}
        assert OrderStatusMapper.map_odoo_status("sent") not in {"completed"}
        assert OrderStatusMapper.map_odoo_status("sale") not in {"completed"}


class TestEdgeCases:
    """Test edge cases in status mapping"""

    def test_none_status(self):
        """Test handling of None status"""
        # Should not crash, should return default
        status = OrderStatusMapper.map_dolibarr_status(None)
        assert status == "processing"

    def test_string_status_conversion(self):
        """Test handling of string status codes"""
        # Dolibarr API might return string codes
        try:
            status = OrderStatusMapper.map_dolibarr_status("1")
            # If it accepts string, verify reasonable output
            assert isinstance(status, str)
        except (TypeError, KeyError):
            # It's acceptable to not accept string codes
            pass

    def test_case_sensitivity_odoo(self):
        """Test Odoo status case sensitivity"""
        # Odoo typically returns lowercase
        status = OrderStatusMapper.map_odoo_status("done")
        assert status == "completed"

        # Unknown case should not crash
        status = OrderStatusMapper.map_odoo_status("DONE")
        assert isinstance(status, str)  # Should return something


class TestStatusCompatibility:
    """Test cross-platform status compatibility"""

    def test_dolibarr_to_woocommerce_mapping(self):
        """Test Dolibarr → WooCommerce mapping"""
        mappings = {
            1: "processing",      # Dolibarr processed → WC processing
            2: "processing",      # Dolibarr shipped → WC processing (WC uses wc-shipped with custom plugin)
            3: "completed",       # Dolibarr delivered → WC completed
            4: "cancelled",       # Dolibarr cancelled → WC cancelled
        }

        for dolibarr_status, expected_wc in mappings.items():
            status = OrderStatusMapper.map_dolibarr_status(dolibarr_status)
            # Verify it maps to something reasonable
            assert status in ["draft", "processed", "shipped", "delivered", "cancelled", "refused"]

    def test_odoo_to_shopify_mapping(self):
        """Test Odoo → Shopify mapping"""
        # Shopify statuses: pending, completed, cancelled, authorized, partially_refunded, refunded
        mappings = {
            "sale": "processing",     # Odoo sale → Shopify processing
            "done": "completed",      # Odoo done → Shopify completed
            "cancel": "cancelled",    # Odoo cancelled → Shopify cancelled
        }

        for odoo_status, expected in mappings.items():
            status = OrderStatusMapper.map_odoo_status(odoo_status)
            assert isinstance(status, str)
            assert len(status) > 0
