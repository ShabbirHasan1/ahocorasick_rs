"""Tests for ahocorasick_rs."""

import pytest

from hypothesis import strategies as st
from hypothesis import given, assume

from ahocorasick_rs import (
    AhoCorasick,
    MATCHKIND_STANDARD,
    MATCHKIND_LEFTMOST_FIRST,
    MATCHKIND_LEFTMOST_LONGEST,
    MatchKind,
    Implementation,
)


@pytest.mark.parametrize("store_patterns", [True, False, None])
@pytest.mark.parametrize(
    "implementation",
    [
        None,
        Implementation.NoncontiguousNFA,
        Implementation.ContiguousNFA,
        Implementation.DFA,
    ],
)
def test_basic_matching(store_patterns, implementation):
    """
    find_matches_as_indexes() and find_matches_as_strings() return matching
    patterns in the given string.
    """
    haystack = "hello, world, hello again"
    patterns = ["hello", "world"]
    if store_patterns is None:
        ac = AhoCorasick(patterns)
    else:
        ac = AhoCorasick(
            patterns, store_patterns=store_patterns, implementation=implementation
        )

    expected = ["hello", "world", "hello"]

    # find_matches_as_indexes()
    index_matches = ac.find_matches_as_indexes(haystack)
    assert [patterns[i] for (i, _, _) in index_matches] == expected
    assert [haystack[s:e] for (_, s, e) in index_matches] == expected

    # find_matches_as_strings()
    assert ac.find_matches_as_strings(haystack) == expected


@pytest.mark.parametrize("store_patterns", [True, False, None])
@pytest.mark.parametrize(
    "implementation",
    [
        None,
        Implementation.NoncontiguousNFA,
        Implementation.ContiguousNFA,
        Implementation.DFA,
    ],
)
def test_unicode(store_patterns, implementation):
    """
    Non-ASCII unicode patterns still give correct results for
    find_matches_as_indexes() and find_matches_as_strings().
    """
    haystack = "hello, world ☃fishá l🤦l"
    patterns = ["d ☃f", "há", "l🤦l"]
    if store_patterns is None:
        ac = AhoCorasick(patterns)
    else:
        ac = AhoCorasick(
            patterns, store_patterns=store_patterns, implementation=implementation
        )
    index_matches = ac.find_matches_as_indexes(haystack)
    expected = ["d ☃f", "há", "l🤦l"]
    assert [patterns[i] for (i, _, _) in index_matches] == expected
    assert [haystack[s:e] for (_, s, e) in index_matches] == expected
    assert ac.find_matches_as_strings(haystack) == expected


@given(st.text(), st.text(min_size=1), st.text(), st.sampled_from([True, False, None]))
def test_unicode_extensive(prefix, pattern, suffix, store_patterns):
    """
    Non-ASCII unicode patterns still give correct results for
    find_matches_as_indexes(), with property-testing.
    """
    assume(pattern not in prefix)
    assume(pattern not in suffix)
    haystack = prefix + pattern + suffix
    if store_patterns is None:
        ac = AhoCorasick([pattern])
    else:
        ac = AhoCorasick([pattern], store_patterns=store_patterns)

    index_matches = ac.find_matches_as_indexes(haystack)
    expected = [pattern]
    assert [i for (i, _, _) in index_matches] == [0]
    assert [haystack[s:e] for (_, s, e) in index_matches] == expected
    assert ac.find_matches_as_strings(haystack) == [pattern]


def test_matchkind():
    """
    Different matchkinds give different results.

    The default, MATCHKIND_STANDARD finds overlapping matches.

    MATCHKIND_LEFTMOST finds the leftmost match if there are overlapping
    matches, choosing the earlier provided pattern.

    MATCHKIND_LEFTMOST finds the leftmost match if there are overlapping
    matches, picking the longest one if there are multiple ones.
    """
    haystack = "This is the winter of my discontent"
    patterns = ["content", "disco", "disc", "discontent", "winter"]

    def get_strings(ac):
        return ac.find_matches_as_strings(haystack)

    # Default is MATCHKIND_STANDARD:
    assert get_strings(AhoCorasick(patterns)) == [
        "winter",
        "disc",
    ]

    # Explicit MATCHKIND_STANDARD:
    assert get_strings(AhoCorasick(patterns, matchkind=MATCHKIND_STANDARD)) == [
        "winter",
        "disc",
    ]
    assert get_strings(AhoCorasick(patterns, matchkind=MatchKind.Standard)) == [
        "winter",
        "disc",
    ]

    # MATCHKIND_LEFTMOST_FIRST:
    assert get_strings(AhoCorasick(patterns, matchkind=MATCHKIND_LEFTMOST_FIRST)) == [
        "winter",
        "disco",
    ]
    assert get_strings(AhoCorasick(patterns, matchkind=MatchKind.LeftmostFirst)) == [
        "winter",
        "disco",
    ]

    # MATCHKIND_LEFTMOST_LONGEST:
    assert get_strings(AhoCorasick(patterns, matchkind=MATCHKIND_LEFTMOST_LONGEST)) == [
        "winter",
        "discontent",
    ]
    assert get_strings(AhoCorasick(patterns, matchkind=MatchKind.LeftmostLongest)) == [
        "winter",
        "discontent",
    ]


def test_overlapping():
    """
    It's possible to get overlapping matches, but only with MATCHKIND_STANDARD.
    """
    haystack = "This is the winter of my discontent"
    patterns = ["content", "disco", "disc", "discontent", "winter"]

    def get_strings(ac):
        assert ac.find_matches_as_strings(haystack) == ac.find_matches_as_strings(
            haystack, overlapping=False
        )
        assert ac.find_matches_as_indexes(haystack) == ac.find_matches_as_indexes(
            haystack, overlapping=False
        )
        result = ac.find_matches_as_strings(haystack, overlapping=True)
        result_indexes = ac.find_matches_as_indexes(haystack, overlapping=True)
        assert [patterns[i] for (i, _, _) in result_indexes] == result
        assert [haystack[s:e] for (_, s, e) in result_indexes] == result
        return result

    def assert_no_overlapping(ac):
        with pytest.raises(ValueError):
            ac.find_matches_as_strings(haystack, overlapping=True)
        with pytest.raises(ValueError):
            ac.find_matches_as_indexes(haystack, overlapping=True)

    # Default is MatchKind.Standard:
    expected = [
        "winter",
        "disc",
        "disco",
        "discontent",
        "content",
    ]
    assert get_strings(AhoCorasick(patterns)) == expected

    # Explicit MATCHKIND_STANDARD:
    assert get_strings(AhoCorasick(patterns, matchkind=MatchKind.Standard)) == expected

    # Other matchkinds don't support overlapping.
    assert_no_overlapping(AhoCorasick(patterns, matchkind=MatchKind.LeftmostFirst))
    assert_no_overlapping(AhoCorasick(patterns, matchkind=MatchKind.LeftmostLongest))
