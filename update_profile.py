"""Generate JinParkmida's GitHub profile card with live public GitHub stats.

Runs via GitHub Actions. Standard library only; no third-party dependencies.
The generated SVGs intentionally use public GitHub data only, so the card
matches what visitors can actually see and does not leak private-repository
counts or private LOC.
"""

import calendar
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

USER = "JinParkmida"
BIRTHDAY = date(1988, 6, 19)
INFO_WIDTH = 58
CARD_WIDTH = 900
CARD_HEIGHT = 520

ART = [
    '                              {   `^   .. ^ .',
    "                          ~'                .  I/!^",
    "                        '                '' )>l->l!',;",
    '                                     `""]~{li]>1<;.;.',
    '                      :        .\'\'  ,i;?l!\'  :^.".. .',
    '                              .`"`\',"`\' i  \'\'`     .',
    '                   ^  \'             \'<l,  .^""^`l,,,;`. .`',
    "                                     .`i_)x{(JjjdmLjtu]`'`^",
    '                   -,          .`:i?|xY0b#WWW88&WM#ahbpY[..`',
    "                   [;       ';?fY0qba**#W8%BBBBB%&WM#*adJ?`.'",
    '                   ("   .\',<]|nUmpkaoo#W&%%BB@BB8&W#**ohbr>"',
    '                       ^;,+]]{/xXOpbaa*#W8%BB%%8W#*oaaahbdni`',
    '                      .:I,-]{{|tnJ0ppk*#MW&%%%%WMooahhhkbdL|;',
    '                      .^,l<_}(|fXLmpk*M*MM8&B%%%W#*aahkbdpOfl',
    '                      .`"Ii+}(txJwko##WM&W&8BBB%&W#*oakbdqQt;',
    '                      .\'"I<)ruvzUZb*W&%&W&W&8B@B%88&WMakdq0x;',
    "                    I .'`l_1/ruzJQmdkaM&M*obpwCXzJQLCUrbkdmu?",
    '                     ..\'```,"^\'^^`^I[xOkaakCj[!:"`<>|/uUhhd0qBq',
    "                     .''''^l)\\jf(-:,;~fJwbpc/(|uLa8&*oqwpahqZ]m",
    "                      ''.'^<1nZh#*wc]~[jCqwLYYJXLdaawddOphhdh*%",
    "                   '..`^'..`.    (^1v?)vq##kQr[]. 'kui[YX*od0o&",
    '                   `..`l<>I,?{-?[-pukxjzhB%Mad}YxXnMaM*&8W*pOW#',
    "                   '  `<(un1Ii-(t1\\QkQCL*@@&&#pf]}/fvq&88&*qd@WQ",
    "                      'l)rJ0OQCUC0dbZJzCa@@8&W##pwpoW8%%WWaZY8%",
    '                     ..^l}jUQbhhhhbqXxuJa@@%&Wa*WWW&888W#aqLC%d',
    "                      .'^I}jLqha*apUI>(O*@@%&kvQk##&8&MobpOJ*8$",
    '                      ...`l1rOwkbpZ/LdX0*%BB8Br)Jwaoohhbw0LCJ',
    "                      ...'^![fXL0OC{)x((Yqbkk##[)/U0ZmOQULQQ0",
    '                      ...\'\'`:>[tncf"\';`:<-?:I+Z0t}|txczuY0QCx',
    "                       .''''^:Iitt-'    ^:-{xh8Wbv\\|1rXULOQC",
    '                       .\'\'`^:>+~~+<:"^I[x/CddpdmLUncU0QQ0CX',
    "                        .'`,>?(}l^'`,,:l|wr|tu_:l{jQwqZ0Uu1",
    '                         .\'`;~1|{!^\' .\'^":u*oddq0uvUYYvu\\^\'',
    '                           .`"l+]]-!`:!|UCZCYvmdmJr\\/t(~"^^"',
    '                            ..`,l>-+:. .^"..}vQZQUc|?I^-^`",;"`',
    '                              ...^!]}]~!>)XqwppwLXjI^-{"`^^`;:,""`',
    '                                ..\'I_|/juzYUQULcr+"I?,"``^",`:""^:,"',
    '                                 ..\'\'^I~~~-[+_i;"I~?,^\'\'```,^::,",,^,""\'',
    '                                   .\'\'\'\'^^^^\'`^,l>\'^\'...\'^,,^:::,""::"""""",',
    ' ......                              .\'\'\'``^^",^.`\'....\'`,,"":;::,""::,,;^","^^:',
    '....\'...                                 .\'^`..\'`\'..\'\'^",,,,,,::::,^"::,^"::,",,\'',
    'x.\'\'\'\'. ..                                  \'\'`\'..\'\'\'"^",:,,,:,,:::,`":::"^",::{',
    ' \'\'`\'..\'\'...                                 .`\'.\'`",",,,""",,,,,:::,^":::,""""',
    '   .\'\'\'\'\'\'.. .                           .     \'^"LX"""""^^""","",::,"^";;::\'',
    '    ^```\'\'..\'.....                              ."*.^^"""^^""",,^",::,"",;;I',
    '      .\'\'\'\'`\'\'.\'......                 ..\'\'....\'. \'^^^^""""""",,"^":::,^^^',
    '        .````\'\'\'\'\'.....            ..  \'...````^"^\'^^^^""""""",,"^^",::`',
    '          ```\'\'\'\'\'\'\'.\'\'..........  .\'. `.,\'^:"^^"^""^^^"","""",,,"^^""',
    '            \'\'````\'\'\'``\'\'.\'\'\'\'\'\'\'.  \'\'\'^"""","^"^"""^`^""",""",,,,"`',
    '              `.````````\'\'\'\'\'\'````..\'\'\'"""^""^^^"^"^```"""""",,,`,',
    '                  ```^^^^`\'\'\'```^^`..\'`""""^""^^^""^`\'`^",,,""',
    '                     ```````````^^`\'..`^"""^^^``^"^^\'\'\'``,`',
]

TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh(url, payload=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-card",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8") if payload is not None else None,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw or b"{}")


def graphql(query, variables=None):
    response = gh(
        "https://api.github.com/graphql",
        {"query": query, "variables": variables or {}},
    )
    if response.get("errors"):
        raise RuntimeError(response["errors"])
    return response["data"]


def age(born, today):
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    months = (today.month - born.month - (today.day < born.day)) % 12
    if today.day >= born.day:
        days = today.day - born.day
    else:
        previous_year, previous_month = (
            (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
        )
        days = calendar.monthrange(previous_year, previous_month)[1] - born.day + today.day
    return years, months, days


def public_repositories():
    repos = []
    page = 1
    while True:
        query = urllib.parse.urlencode(
            {"type": "owner", "sort": "updated", "per_page": 100, "page": page}
        )
        batch = gh(f"https://api.github.com/users/{USER}/repos?{query}")
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected repository response: {batch!r}")
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def commit_contributions(joined_year):
    now = datetime.now(timezone.utc)
    aliases = "\n".join(
        f'y{year}: contributionsCollection(from: "{year}-01-01T00:00:00Z", '
        f'to: "{(str(year + 1) + "-01-01T00:00:00Z") if year < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")}") '
        "{ totalCommitContributions }"
        for year in range(joined_year, now.year + 1)
    )
    data = graphql(f'query {{ user(login: "{USER}") {{ {aliases} }} }}')["user"]
    return sum(collection["totalCommitContributions"] for collection in data.values())


LOC_QUERY = """
query($owner: String!, $name: String!, $id: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, author: {id: $id}, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes { additions deletions }
          }
        }
      }
    }
  }
}
"""


def lines_of_code(repos, user_node_id):
    additions = deletions = 0
    failures = 0
    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        cursor = None
        try:
            while True:
                data = graphql(
                    LOC_QUERY,
                    {"owner": USER, "name": name, "id": user_node_id, "cursor": cursor},
                )
                repository = data.get("repository")
                if not repository or repository.get("defaultBranchRef") is None:
                    break
                history = repository["defaultBranchRef"]["target"]["history"]
                additions += sum(node["additions"] for node in history["nodes"])
                deletions += sum(node["deletions"] for node in history["nodes"])
                if not history["pageInfo"]["hasNextPage"]:
                    break
                cursor = history["pageInfo"]["endCursor"]
        except Exception as exc:
            # One inaccessible/odd repository should not prevent the entire card updating.
            failures += 1
            print(f"LOC warning for {name}: {exc}", file=sys.stderr)
    return {
        "loc_add": additions,
        "loc_del": deletions,
        "loc": additions - deletions,
        "loc_partial": failures > 0,
    }


def fetch_stats():
    user = gh(f"https://api.github.com/users/{USER}")
    repos = public_repositories()
    joined_year = int(user["created_at"][:4])

    stats = {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(repo.get("stargazers_count", 0) for repo in repos),
        "commits": commit_contributions(joined_year),
    }
    stats.update(lines_of_code(repos, user["node_id"]))
    return stats


PALETTES = {
    "dark": {
        "bg": "#0d1117",
        "border": "#30363d",
        "art": "#8b949e",
        "h": "#58a6ff",
        "k": "#ffa657",
        "v": "#c9d1d9",
        "d": "#484f58",
        "g": "#3fb950",
        "r": "#f85149",
    },
    "light": {
        "bg": "#ffffff",
        "border": "#d0d7de",
        "art": "#57606a",
        "h": "#0969da",
        "k": "#953800",
        "v": "#24292f",
        "d": "#afb8c1",
        "g": "#1a7f37",
        "r": "#cf222e",
    },
}


def kv(key, value, width=INFO_WIDTH):
    value = str(value)
    dots = "." * max(width - len(key) - len(value) - 3, 1)
    return [(f"{key}: ", "k"), (dots + " ", "d"), (value, "v")]


def kv2(key1, value1, key2, value2):
    return kv(key1, value1, 29) + [(" | ", "d")] + kv(key2, value2, 26)


def rule(title=""):
    label = f"─ {title} " if title else ""
    return [(label, "h"), ("─" * max(INFO_WIDTH - len(label), 1), "d")]


def number(value):
    return f"{value:,}" if isinstance(value, int) else str(value)


def info_lines(stats):
    years, months, days = age(BIRTHDAY, date.today())
    return [
        [(f"{USER.lower()}@github ", "h"), ("─" * (INFO_WIDTH - len(USER) - 8), "d")],
        [],
        kv("OS", "Windows 11", "Kali Linux")
        kv("Uptime", f"{years} years, {months} months, {days} days"),
        kv("Role", "B.Sc. CS student · Dev · Researcher"),
        kv("Location", "Scandinavia"),
        kv("IDE", "Codex · VS Code Insiders · Obsidian · Notepad++"),
        [],
        kv("Languages.Code", "Python · C · C# · Rust · TypeScript"),
        kv("Languages.Real", "Danish · English · Korean (learning)"),
        kv("Focus", "Cybersecurity · AI · Systems design"),
        [],
        rule("GitHub Stats"),
        kv2("Public repos", number(stats["repos"]), "Followers", number(stats["followers"])),
        kv2("Commits", number(stats["commits"]), "Stars received", number(stats["stars"])),
        [
            ("Lines of Code: ", "k"),
            (("~" if stats.get("loc_partial") else "") + number(stats["loc"]), "v"),
            (" ( ", "d"),
            (number(stats["loc_add"]) + "++", "g"),
            (", ", "d"),
            (number(stats["loc_del"]) + "--", "r"),
            (" )", "d"),
        ],
    ]


def render(mode, stats):
    palette = PALETTES[mode]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_WIDTH}" height="{CARD_HEIGHT}" '
        f'viewBox="0 0 {CARD_WIDTH} {CARD_HEIGHT}" role="img" '
        f'aria-label="Jin Park GitHub profile card">',
        f'<rect x="0.5" y="0.5" width="{CARD_WIDTH - 1}" height="{CARD_HEIGHT - 1}" rx="10" '
        f'fill="{palette["bg"]}" stroke="{palette["border"]}"/>',
        '<g font-family="Consolas, Menlo, Monaco, ui-monospace, monospace" '
        f'font-size="7.1px" fill="{palette["art"]}">',
    ]
    for index, line in enumerate(ART):
        out.append(
            f'<text x="18" y="{26 + index * 8.8:.1f}" xml:space="preserve">'
            f'{html.escape(line)}</text>'
        )
    out.append("</g>")

    for index, segments in enumerate(info_lines(stats)):
        if not segments:
            continue
        spans = "".join(
            f'<tspan fill="{palette[color]}">{html.escape(text)}</tspan>'
            for text, color in segments
        )
        out.append(
            '<text x="400" '
            f'y="{43 + index * 25}" font-family="Consolas, Menlo, Monaco, ui-monospace, monospace" '
            f'font-size="12.5px" xml:space="preserve">{spans}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


def selfcheck():
    assert USER == "JinParkmida"
    assert BIRTHDAY == date(1988, 6, 19)
    assert age(date(1989, 1, 15), date(2026, 7, 10)) == (37, 5, 25)
    assert age(date(2000, 3, 31), date(2026, 4, 1)) == (26, 0, 1)
    assert age(date(2000, 1, 1), date(2026, 1, 1)) == (26, 0, 0)
    assert len(ART) == 52
    assert max(map(len, ART)) <= 81


def write_cards(stats):
    for mode in PALETTES:
        with open(f"{mode}_mode.svg", "w", encoding="utf-8") as file:
            file.write(render(mode, stats))


if __name__ == "__main__":
    selfcheck()
    if "--preview" in sys.argv:
        # Only for local layout testing. GitHub Actions never uses these placeholders.
        stats = {
            "repos": 100,
            "followers": 6,
            "stars": "live",
            "commits": "live",
            "loc": "live",
            "loc_add": "live",
            "loc_del": "live",
            "loc_partial": False,
        }
    else:
        stats = fetch_stats()
        print("stats:", stats)
    write_cards(stats)
    print("wrote dark_mode.svg, light_mode.svg")
