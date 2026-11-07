from pathlib import Path

import pytest

from app.ingestion import seed
from app.repository import Repository
from app.store import InMemoryStore

DATA = Path(__file__).parent / "data"


@pytest.fixture
def repo() -> Repository:
    return Repository(InMemoryStore())


@pytest.fixture
def seeded(repo, tmp_path):
    """Host (sample.gff3) and a donor genome with one overlapping-style gene, both with proteins."""
    donor_gff = tmp_path / "donor.gff3"
    donor_gff.write_text(
        "##gff-version 3\n"
        "##sequence-region\tD1\t1\t9000\n"
        "D1\tt\tgene\t100\t900\t.\t+\t.\tID=SbarKPS1;Name=KPS1\n"
        "D1\tt\tgene\t2000\t2600\t.\t-\t.\tID=SbarX1\n"
    )
    host_prot = tmp_path / "host.faa"
    host_prot.write_text(">SbaiKPS1\nMKVLAAGG\n>SbaiCHS1.t1\nMTTTT\n>orphan\nMMMM\n")
    donor_prot = tmp_path / "donor.faa"
    donor_prot.write_text(">SbarKPS1\nMKVLAAGA\n")
    host_plan = seed.build_plan(
        "Host sp.", "host", "ACC-H", "test", DATA / "sample.gff3", host_prot, strip_isoform=True
    )
    donor_plan = seed.build_plan("Donor sp.", "donor", "ACC-D", "test", donor_gff, donor_prot)
    seed.apply_plan(repo, host_plan)
    seed.apply_plan(repo, donor_plan)
    return repo
