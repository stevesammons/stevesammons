"""Python port of WordPress's wpautop() (wp-includes/formatting.php), used to turn a classic-editor
post into explicit HTML before block markup is added (once a post has blocks, WordPress stops
running wpautop on it). apply.py checks every conversion by comparing rendered output."""
import re

ALLBLOCKS = ("(?:table|thead|tfoot|caption|col|colgroup|tbody|tr|td|th|div|dl|dd|dt|ul|ol|li|pre|form|map|"
             "area|blockquote|address|style|p|h[1-6]|hr|fieldset|legend|section|article|aside|hgroup|"
             "header|footer|nav|figure|figcaption|details|menu|summary)")


def _replace_in_html_tags(text, pairs):
    parts = re.split(r"(<[^>]*>|<!--.*?-->)", text, flags=re.S)
    for i in range(1, len(parts), 2):
        for a, b in pairs.items():
            parts[i] = parts[i].replace(a, b)
    return "".join(parts)


def wpautop(text, br=True):
    if text.strip() == "":
        return ""
    text = text + "\n"
    pre_tags = {}
    if "<pre" in text:
        chunks = text.split("</pre>")
        last = chunks.pop()
        text = ""
        for i, chunk in enumerate(chunks):
            start = chunk.find("<pre")
            if start == -1:
                text += chunk
                continue
            name = f"<pre wp-pre-tag-{i}></pre>"
            pre_tags[name] = chunk[start:] + "</pre>"
            text += chunk[:start] + name
        text += last
    text = re.sub(r"<br\s*/?>\s*<br\s*/?>", "\n\n", text)
    text = re.sub(r"(<" + ALLBLOCKS + r"[\s/>])", r"\n\n\1", text)
    text = re.sub(r"(</" + ALLBLOCKS + r">)", r"\1\n\n", text)
    text = re.sub(r"(<hr\s*?/?>)", r"\1\n\n", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _replace_in_html_tags(text, {"\n": " <!-- wpnl --> "})
    if "<option" in text:
        text = re.sub(r"\s*<option", "<option", text)
        text = re.sub(r"</option>\s*", "</option>", text)
    if "</object>" in text:
        text = re.sub(r"(<object[^>]*>)\s*", r"\1", text)
        text = re.sub(r"\s*</object>", "</object>", text)
        text = re.sub(r"\s*(</?(?:param|embed)[^>]*>)\s*", r"\1", text)
    if "<source" in text or "<track" in text:
        text = re.sub(r"([<\[](?:audio|video)[^>\]]*[>\]])\s*", r"\1", text)
        text = re.sub(r"\s*([<\[]/(?:audio|video)[>\]])", r"\1", text)
        text = re.sub(r"\s*(<(?:source|track)[^>]*>)\s*", r"\1", text)
    if "<figcaption" in text:
        text = re.sub(r"\s*(<figcaption[^>]*>)", r"\1", text)
        text = re.sub(r"</figcaption>\s*", "</figcaption>", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    paras = [p for p in re.split(r"\n\s*\n", text) if p != ""]
    text = ""
    for p in paras:
        text += "<p>" + p.strip("\n") + "</p>\n"
    text = re.sub(r"<p>\s*</p>", "", text)
    text = re.sub(r"<p>([^<]+)</(div|address|form)>", r"<p>\1</p></\2>", text)
    text = re.sub(r"<p>\s*(</?" + ALLBLOCKS + r"[^>]*>)\s*</p>", r"\1", text)
    text = re.sub(r"<p>(<li.+?)</p>", r"\1", text)
    text = re.sub(r"<p><blockquote([^>]*)>", r"<blockquote\1><p>", text, flags=re.I)
    text = text.replace("</blockquote></p>", "</p></blockquote>")
    text = re.sub(r"<p>\s*(</?" + ALLBLOCKS + r"[^>]*>)", r"\1", text)
    text = re.sub(r"(</?" + ALLBLOCKS + r"[^>]*>)\s*</p>", r"\1", text)
    if br:
        text = re.sub(r"<(script|style|svg|math).*?</\1>", lambda m: m.group(0).replace("\n", "<WPPreserveNewline />"),
                      text, flags=re.S)
        text = text.replace("<br>", "<br />").replace("<br/>", "<br />")
        text = re.sub(r"(?<!<br />)\s*\n", "<br />\n", text)
        text = text.replace("<WPPreserveNewline />", "\n")
    text = re.sub(r"(</?" + ALLBLOCKS + r"[^>]*>)\s*<br />", r"\1", text)
    text = re.sub(r"<br />(\s*</?(?:p|li|div|dl|dd|dt|th|pre|td|ul|ol)[^>]*>)", r"\1", text)
    text = re.sub(r"\n</p>$", "</p>", text)
    for name, pre in pre_tags.items():
        text = text.replace(name, pre)
    if "<!-- wpnl -->" in text:
        text = text.replace(" <!-- wpnl --> ", "\n").replace("<!-- wpnl -->", "\n")
    return text
