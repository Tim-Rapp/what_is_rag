from coryat.clues import Clue, clean, exclusion_reason, load_all, make_id


def make_clue(clue_text="Scottish word for lake", gold="loch"):
    return Clue(
        id="x", round=1, category="LAKES & RIVERS", comments="",
        clue_text=clue_text, gold=gold, air_date="1984-09-10",
    )


def test_clean_unescapes_quotes_and_html():
    assert clean('this kind of "bias\\"') == 'this kind of "bias"'
    assert clean('\\"Golden" brewer') == '"Golden" brewer'
    assert clean("Ant&ocirc;nio Carlos Jobim") == "Antônio Carlos Jobim"
    assert clean("  padded  ") == "padded"


def test_make_id_is_stable():
    a = make_id("1984-09-10", "1", "LAKES & RIVERS", "Scottish word for lake")
    b = make_id("1984-09-10", "1", "LAKES & RIVERS", "Scottish word for lake")
    assert a == b and len(a) == 12


def test_exclusion_reasons():
    assert exclusion_reason(make_clue()) is None
    assert exclusion_reason(make_clue(gold="")) == "ungradable"
    assert exclusion_reason(make_clue(gold="@")) == "ungradable"
    assert exclusion_reason(make_clue("This river, seen here, flows south")) == "media"
    assert exclusion_reason(make_clue("(Sarah of the Clue Crew reports.) This...")) == "media"
    assert exclusion_reason(make_clue("He's the current Speaker of the House")) == "time_sensitive"


def test_load_all_renames_columns(tmp_path):
    tsv = tmp_path / "clues.tsv"
    tsv.write_text(
        "round\tclue_value\tdaily_double_value\tcategory\tcomments\tanswer\tquestion\tair_date\tnotes\n"
        "1\t200\t0\tLAKES & RIVERS\t\tScottish word for lake\tloch\t1984-09-10\t\n"
        '3\t0\t0\tSONGS\t(Alex: Hawaiian.)\tThis "farewell to thee\\"\t\\"Aloha &#699;Oe\\"\t2020-01-01\t\n',
        encoding="utf-8",
    )
    first, second = load_all(tsv)
    assert (first.clue_text, first.gold, first.round) == ("Scottish word for lake", "loch", 1)
    assert second.gold == '"Aloha ʻOe"'
    assert second.comments == "(Alex: Hawaiian.)"
    assert second.round == 3
