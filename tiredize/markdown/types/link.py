# Standard library
from __future__ import annotations
from dataclasses import dataclass
import re

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.types.code import CodeInline
from tiredize.markdown.types.image import InlineImage
from tiredize.markdown.types.reference import ReferenceDefinition
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


def _blank_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """
    Replace the given (start, end) spans of `text` with spaces,
    preserving length and every other character. Spans never contain
    newlines: whitespace ends both kinds of autolink.
    """
    result = ""
    last_end = 0
    for start, end in spans:
        result += text[last_end:start] + " " * (end - start)
        last_end = end
    return result + text[last_end:]


@dataclass(frozen=False)
class Autolink:
    """
    An autolink per GFM 0.29-gfm section 6.8: an absolute URI or an
    email address between `<` and `>`.

    `string` is the matched text including the brackets. `url` is
    the link target: the URI as written for a URI autolink, or
    `mailto:` followed by the address for an email autolink.
    Backslashes inside the brackets are literal characters, never
    escapes.
    """
    position: Position
    string: str
    url: str

    # An absolute URI is a scheme, a colon, and any characters other
    # than ASCII whitespace, ASCII control characters, `<` and `>`.
    # A scheme is 2-32 characters: an ASCII letter, then ASCII
    # letters, digits, `+`, `.` or `-`.
    #
    # An email address is anything matching the non-normative HTML5
    # regex reproduced in the specification. Its domain labels are
    # optional (`<x@y>` is an email autolink), each label is 1-63
    # characters and may not start or end with a hyphen.
    #
    # The URI branch is tried first, so `<mailto:x@y.z>` is a URI
    # whose target is written as-is (spec example 606), while
    # `<x@y.z>` is an email whose target gains the `mailto:` prefix.
    RE_AUTOLINK = r"""
        <                                   # Opening angle bracket
        (?:
            (?P<uri>
                [A-Za-z][A-Za-z0-9+.\-]{1,31}   # Scheme, 2-32 characters
                :                               # Colon
                [^\x00-\x20\x7F<>]*             # No ASCII space/control/<>
            )
          | (?P<email>
                [a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+    # Local part
                @
                [a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?   # First label
                (?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*  # More
            )
        )
        >                                   # Closing angle bracket
    """

    # Static methods
    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[Autolink]:
        """
        Extract autolinks from markdown text.

        Code blocks and inline code are blanked first, so a bracketed
        URI inside backticks is not a link.
        """
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        matches = search_all_re(
            Autolink.RE_AUTOLINK,
            text_sanitized
        )

        result: list[Autolink] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            uri = match.group("uri")
            if uri is not None:
                url = uri
            else:
                url = "mailto:" + match.group("email")

            result.append(
                Autolink(
                    position=position,
                    string=match.group(),
                    url=url
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Autolinks with whitespace

        Blanks exactly the spans `extract()` reports for `text`, so a
        bracketed URI inside code is left alone here too.
        """
        return _blank_spans(text, [
            (link.position.offset, link.position.offset + link.position.length)
            for link in Autolink.extract(text)
        ])


@dataclass(frozen=False)
class ExtendedAutolink:
    """
    An extended autolink per GFM 0.29-gfm section 6.9: a URL, email
    address or `mailto:`/`xmpp:` address recognised in running text
    without angle brackets.

    A match is recognised only at the start of the text, after
    whitespace, or after one of `*`, `_`, `~`, `(`, and is one of:

    - `www.` + a valid domain + an optional path;
    - `http://` or `https://` + a valid domain + an optional path;
    - an email address;
    - `mailto:` or `xmpp:` + an email address, where `xmpp:` allows
      one `/resource` after the address.

    A valid domain is segments of alphanumerics, `_` and `-`
    separated by `.`, with at least one `.` and no `_` in the last
    two segments. The path runs to the next whitespace or `<` and is
    then trimmed by extended autolink path validation (see `_trim`).

    The specification never defines "alphanumeric", so cmark-gfm
    breaks the tie: `www.` and `http(s)` domains accept Unicode
    letters and digits, while email addresses -- bare, `mailto:` and
    `xmpp:`, resource included -- are ASCII only.

    `string` is the matched text after trimming, exactly as it
    appears in the source. `url` is the link target GitHub would
    navigate to: `string` unchanged for `http`, `https`, `mailto:`
    and `xmpp:`; `http://` + `string` for `www.`; `mailto:` +
    `string` for a bare email address.

    `./`, `../` and backslash-prefixed tokens are never matched:
    GitHub renders them as text, and a backslash in GFM is an escape,
    not a path separator.
    """
    position: Position
    string: str
    url: str

    # Candidate finder. Each alternative captures the longest run the
    # specification allows; `_scan` then validates the domain and
    # trims the tail, because those rules are procedural (count
    # parentheses, check the last two domain segments) and are not
    # expressible in one pattern.
    #
    # "Alphanumeric" follows cmark-gfm where the specification is
    # silent: the email alternative uses ASCII `[A-Za-z0-9]` in the
    # local part, the domain and the xmpp resource (cmark-gfm checks
    # them with `isalnum`), whereas the www/url domain in `RE_DOMAIN`
    # uses `\w` (cmark-gfm's host check is Unicode-aware), so
    # internationalised domain names link as they do on GitHub.
    #
    # The email alternative's domain and xmpp resource are written as
    # non-empty segments joined by `.`, so a trailing `.` -- or a `.`
    # followed by anything but a segment character -- is left outside
    # the match rather than trimmed afterwards (spec example 632).
    RE_CANDIDATE = r"""
        (?:\A|(?<=[\s*_~(]))             # Start, whitespace, or * _ ~ (
        (?:
            (?P<www>www\.[^\s<]*)         # www. then to whitespace or <
          | (?P<url>(?i:https?)://[^\s<]*)   # http(s):// likewise
          | (?P<protocol>mailto:|xmpp:)?  # Optional protocol, lower-case
            (?P<local>[A-Za-z0-9._+-]+)   # Local part, ASCII only
            @
            (?P<domain>                   # Domain segments, ASCII only
                [A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*
            )
            (?P<resource>                 # xmpp /resource, ASCII only
                /[A-Za-z0-9@]+(?:\.[A-Za-z0-9@]+)*
            )?
        )
    """

    # The leading part of a www/url candidate that must be a valid
    # domain: segments of alphanumerics, `_` and `-` joined by `.`.
    # `\w` here is deliberate: unlike the email domain above, this
    # one is Unicode-aware (see the note on RE_CANDIDATE).
    RE_DOMAIN = r"""
        [\w-]+(?:\.[\w-]+)*
    """

    # An entity-like tail: `&`, one or more alphanumerics, `;` at the
    # very end of the candidate.
    RE_ENTITY_TAIL = r"""
        &[^\W_]+;\Z
    """

    # Trailing characters that are never part of an extended autolink.
    TRAILING_PUNCTUATION = "?!.,:*_~"

    # Static methods
    @staticmethod
    def _scan(text: str) -> list[tuple[int, int, str]]:
        """
        Find every extended autolink in `text` as (start, end, url).

        Candidates are validated in order of position. A rejected
        candidate is skipped by one character rather than by its
        whole length, so a valid link that starts inside it after a
        delimiter (for example `http://nodot(www.a.b)`) is still
        found. Scanning resumes after the trimmed end of an accepted
        link.
        """
        pattern = re.compile(ExtendedAutolink.RE_CANDIDATE, re.VERBOSE)
        result: list[tuple[int, int, str]] = []
        pos = 0
        while pos <= len(text):
            match = pattern.search(text, pos)
            if match is None:
                break
            found = ExtendedAutolink._validate(match)
            if found is None:
                pos = match.start() + 1
                continue
            end, url = found
            result.append((match.start(), end, url))
            pos = end
        return result

    @staticmethod
    def _trim(candidate: str) -> int:
        """
        Apply extended autolink path validation to a www/url
        candidate and return the length that survives.

        Working from the end, repeatedly:

        - drop a trailing `?`, `!`, `.`, `,`, `:`, `*`, `_` or `~`;
        - drop a trailing `)` only while the candidate holds more
          `)` than `(` (counted once, over the whole candidate);
        - drop a trailing `&` + alphanumerics + `;`, which looks like
          an entity reference.

        Any other final character ends the trimming. A lone `;`, `'`
        or `"` is kept: the specification lists none of them,
        although cmark-gfm strips them.
        """
        opening = candidate.count("(")
        closing = candidate.count(")")
        end = len(candidate)
        while end > 0:
            last = candidate[end - 1]
            if last in ExtendedAutolink.TRAILING_PUNCTUATION:
                end -= 1
            elif last == ")":
                if closing <= opening:
                    break
                closing -= 1
                end -= 1
            elif last == ";":
                entity = re.search(
                    ExtendedAutolink.RE_ENTITY_TAIL,
                    candidate[:end],
                    re.VERBOSE
                )
                if entity is None:
                    break
                end = entity.start()
            else:
                break
        return end

    @staticmethod
    def _valid_domain(domain: str) -> bool:
        """
        A valid domain has at least one `.` and no `_` in its last
        two segments.
        """
        segments = domain.split(".")
        if len(segments) < 2:
            return False
        return "_" not in segments[-1] and "_" not in segments[-2]

    @staticmethod
    def _valid_email_domain(domain: str) -> bool:
        """
        An email domain has at least one `.` and does not end in `-`
        or `_`. Its segments are already non-empty by construction.
        """
        return "." in domain and domain[-1] not in "-_"

    @staticmethod
    def _validate(match: re.Match[str]) -> tuple[int, str] | None:
        """
        Turn a candidate match into (end, url), or None to reject it.
        """
        if match.group("www") is not None or match.group("url") is not None:
            return ExtendedAutolink._validate_url(match)
        return ExtendedAutolink._validate_email(match)

    @staticmethod
    def _validate_email(match: re.Match[str]) -> tuple[int, str] | None:
        """
        Validate an email or protocol candidate.

        The domain must be valid as a whole; a bad one (ending in `-`
        or `_`, spec example 632) rejects the candidate outright
        rather than shortening it. Only `xmpp:` keeps a `/resource`.
        """
        if not ExtendedAutolink._valid_email_domain(match.group("domain")):
            return None
        end = match.end("domain")
        if match.group("protocol") == "xmpp:" and match.group("resource"):
            end = match.end("resource")
        string = match.string[match.start():end]
        if match.group("protocol") is None:
            return end, "mailto:" + string
        return end, string

    @staticmethod
    def _validate_url(match: re.Match[str]) -> tuple[int, str] | None:
        """
        Validate a `www.` or `http(s)://` candidate.

        The domain is the longest domain-shaped prefix after the
        scheme (for `www.`, the `www` segment is part of it). If it
        is valid, the whole run is trimmed by `_trim`.
        """
        www = match.group("www")
        candidate = www if www is not None else match.group("url")
        domain_start = 0 if www is not None else candidate.index("//") + 2
        domain = re.match(
            ExtendedAutolink.RE_DOMAIN,
            candidate[domain_start:],
            re.VERBOSE
        )
        if domain is None:
            return None
        if not ExtendedAutolink._valid_domain(domain.group()):
            return None
        end = match.start() + ExtendedAutolink._trim(candidate)
        string = match.string[match.start():end]
        if www is not None:
            return end, "http://" + string
        return end, string

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[ExtendedAutolink]:
        """
        Extract extended autolinks from markdown text.

        Code blocks, inline code, images, autolinks, inline links and
        reference definitions are blanked first, so a URL inside
        `[text](url)` or `<url>` is never also an extended autolink.
        """
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        text_sanitized = InlineImage.sanitize(text_sanitized)
        text_sanitized = Autolink.sanitize(text_sanitized)
        text_sanitized = InlineLink.sanitize(text_sanitized)
        text_sanitized = ReferenceDefinition.sanitize(text_sanitized)

        result: list[ExtendedAutolink] = []
        for start, end, url in ExtendedAutolink._scan(text_sanitized):
            result.append(
                ExtendedAutolink(
                    position=Position(
                        offset=base_offset + start,
                        length=end - start
                    ),
                    string=text[start:end],
                    url=url
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Extended Autolinks with whitespace

        Blanks exactly the spans `extract()` reports for `text`.
        """
        return _blank_spans(text, [
            (link.position.offset, link.position.offset + link.position.length)
            for link in ExtendedAutolink.extract(text)
        ])


@dataclass(frozen=False)
class InlineLink:
    position: Position
    string: str
    title: str
    url: str

    RE_LINK_INLINE = r"""
        (?<!!)                        # Negative lookbehind to avoid images
        \[\s*                         # Opening bracket and whitespace
        (?P<text>[^]]*?)              # Capture the title
        \s*                           # Optional whitespace
        \]\(                          # Closing bracket, opening parenthesis
        \s*                           # Optional whitespace
        (?P<url>[^\s)]+)               # Capture the URL
        (\s*?\"(?P<title>[^"]*?)\")?  # Capture optional title
        \s*\)                         # Closing parenthesis
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[InlineLink]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        matches = search_all_re(
            InlineLink.RE_LINK_INLINE,
            text_sanitized
        )

        result: list[InlineLink] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            result.append(
                InlineLink(
                    position=position,
                    string=match.group(),
                    title=match.group("title"),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Inline Links with whitespace
        """
        return sanitize_text(InlineLink.RE_LINK_INLINE, text)
