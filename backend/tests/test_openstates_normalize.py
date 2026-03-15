"""Unit tests for normalize_il_name() in app.imports.sources.openstates."""

from app.imports.sources.openstates import normalize_il_name


class TestNormalizeIlName:
    def test_basic_name(self):
        assert normalize_il_name("Don Harmon") == "don harmon"

    def test_middle_initial(self):
        assert normalize_il_name("Marcus C. Evans") == "marcus evans"

    def test_honorific_rep_abbreviated(self):
        assert normalize_il_name("Rep. Anna Moeller") == "anna moeller"

    def test_honorific_rep_full(self):
        assert normalize_il_name("Representative Anna Moeller") == "anna moeller"

    def test_honorific_sen_abbreviated(self):
        assert normalize_il_name("Sen. Don Harmon") == "don harmon"

    def test_honorific_sen_full(self):
        assert normalize_il_name("Senator Don Harmon") == "don harmon"

    def test_suffix_jr_with_period(self):
        assert normalize_il_name("Fred Crespo Jr.") == "fred crespo"

    def test_suffix_sr(self):
        assert normalize_il_name("Fred Crespo Sr") == "fred crespo"

    def test_suffix_ii(self):
        assert normalize_il_name("Bob Smith II") == "bob smith"

    def test_suffix_iii(self):
        assert normalize_il_name("Bob Smith III") == "bob smith"

    def test_suffix_iv(self):
        assert normalize_il_name("Bob Smith IV") == "bob smith"

    def test_punctuation_apostrophe(self):
        # Apostrophe removed, no space inserted → "obrien"
        assert normalize_il_name("O'Brien Kelly") == "obrien kelly"

    def test_hyphenated_name(self):
        # Hyphen is punctuation; removed without space → "annmarie"
        assert normalize_il_name("Ann-Marie Keenan") == "annmarie keenan"

    def test_extra_whitespace(self):
        assert normalize_il_name("Bob   Smith") == "bob smith"

    def test_mixed_case(self):
        assert normalize_il_name("ANNA MOELLER") == "anna moeller"

    def test_already_normalized_is_idempotent(self):
        once = normalize_il_name("Anna Moeller")
        twice = normalize_il_name(once)
        assert once == twice

    def test_middle_initial_from_real_example(self):
        # Marcus C. Evans Jr. → "marcus evans"
        assert normalize_il_name("Marcus C. Evans Jr.") == "marcus evans"
