from __future__ import annotations

import unittest

from app.world_id import verify_world_id_proof


class WorldIdTests(unittest.IsolatedAsyncioTestCase):
    async def test_mock_accepted_in_demo_mode(self) -> None:
        self.assertTrue(await verify_world_id_proof({"is_mock": True}))

    async def test_empty_proof_rejected(self) -> None:
        self.assertFalse(await verify_world_id_proof({}))
        self.assertFalse(await verify_world_id_proof(None))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
