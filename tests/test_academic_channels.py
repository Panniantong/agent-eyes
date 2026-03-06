# -*- coding: utf-8 -*-
"""Tests for academic channels: arXiv, bioRxiv, PubMed."""

import pytest
from agent_reach.channels.arxiv import ArxivChannel
from agent_reach.channels.biorxiv import BiorxivChannel
from agent_reach.channels.pubmed import PubMedChannel


class TestArxivChannel:
    def setup_method(self):
        self.ch = ArxivChannel()

    def test_can_handle_arxiv_url(self):
        assert self.ch.can_handle("https://arxiv.org/abs/2410.05390")
        assert self.ch.can_handle("http://arxiv.org/pdf/2410.05390")
        assert self.ch.can_handle("https://export.arxiv.org/api/query")

    def test_cannot_handle_other_url(self):
        assert not self.ch.can_handle("https://github.com/test/repo")
        assert not self.ch.can_handle("https://pubmed.ncbi.nlm.nih.gov/12345/")
        assert not self.ch.can_handle("https://www.google.com")

    def test_check_returns_tuple(self):
        result = self.ch.check()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] in ("ok", "warn", "off", "error")
        assert isinstance(result[1], str)

    def test_metadata(self):
        assert self.ch.name == "arxiv"
        assert self.ch.tier == 0
        assert "arXiv" in self.ch.backends[0]


class TestBiorxivChannel:
    def setup_method(self):
        self.ch = BiorxivChannel()

    def test_can_handle_biorxiv_url(self):
        assert self.ch.can_handle("https://www.biorxiv.org/content/10.1101/2024.01.01")
        assert self.ch.can_handle("https://biorxiv.org/content/xxx")

    def test_can_handle_medrxiv_url(self):
        assert self.ch.can_handle("https://www.medrxiv.org/content/10.1101/2024.01.01")
        assert self.ch.can_handle("https://medrxiv.org/content/xxx")

    def test_cannot_handle_other_url(self):
        assert not self.ch.can_handle("https://arxiv.org/abs/2410.05390")
        assert not self.ch.can_handle("https://github.com/test")

    def test_check_returns_tuple(self):
        result = self.ch.check()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] in ("ok", "warn", "off", "error")

    def test_metadata(self):
        assert self.ch.name == "biorxiv"
        assert self.ch.tier == 0
        assert "bioRxiv" in self.ch.backends[0]


class TestPubMedChannel:
    def setup_method(self):
        self.ch = PubMedChannel()

    def test_can_handle_pubmed_url(self):
        assert self.ch.can_handle("https://pubmed.ncbi.nlm.nih.gov/12345/")
        assert self.ch.can_handle("https://pubmed.ncbi.nlm.nih.gov/12345678")

    def test_can_handle_ncbi_url(self):
        assert self.ch.can_handle("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123/")
        assert self.ch.can_handle("https://ncbi.nlm.nih.gov/gene/1234")

    def test_cannot_handle_other_url(self):
        assert not self.ch.can_handle("https://arxiv.org/abs/2410.05390")
        assert not self.ch.can_handle("https://www.biorxiv.org/content/xxx")

    def test_check_returns_tuple(self):
        result = self.ch.check()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] in ("ok", "warn", "off", "error")

    def test_metadata(self):
        assert self.ch.name == "pubmed"
        assert self.ch.tier == 0
        assert "Entrez" in self.ch.backends[0]
