from io import StringIO

from catleg.law_text_fr import ArticleType, find_id_in_string, parse_article_id
from catleg.parse_catala_markdown import _make_markdown_parser, parse_catala_file
from mdformat.renderer import MDRenderer


def test_parse_article_id():
    typ, id = parse_article_id("legiarti000038814944")
    assert typ == ArticleType.LEGIARTI
    assert id == "legiarti000038814944"


def test_find_id_in_string():
    assert find_id_in_string("####### Article R821-2 | LEGIARTI000038879021") == (
        ArticleType.LEGIARTI,
        "LEGIARTI000038879021",
    )
    assert find_id_in_string("###### Article L841-1 | LEGIARTI000038814864") == (
        ArticleType.LEGIARTI,
        "LEGIARTI000038814864",
    )
    assert find_id_in_string("This definitely does not match") is None


catala_text = """
###### Article L822-2 | LEGIARTI000038814944

I.-Peuvent bénéficier d'une aide personnelle au logement :

1° Les personnes de nationalité française ;

2° Les personnes de nationalité étrangère remplissant les conditions
prévues par les deux premiers alinéas de l' article M. 512-2 du
code de la sécurité sociale .

```catala
champ d'application ÉligibilitéAidesPersonnelleLogement:
  définition condition_nationalité égal à
    selon demandeur.nationalité sous forme
    -- Française: vrai
    -- Étrangère de conditions:
      conditions.satisfait_conditions_l512_2_code_sécurité_sociale
```

II.-Parmi les personnes mentionnées au I, peuvent bénéficier d'une aide
personnelle au logement celles remplissant les conditions prévues par le
présent livre pour son attribution qui sont locataires, résidents en
logement-foyer ou qui accèdent à la propriété d'un local à usage exclusif
d'habitation et constituant leur résidence principale.

Les sous-locataires, sous les mêmes conditions, peuvent également en bénéficier.

```catala
champ d'application ÉligibilitéAidesPersonnelleLogement:
  étiquette l822_2 règle condition_logement_mode_occupation sous condition
    selon ménage.logement.mode_occupation sous forme
      -- Locataire: vrai
      -- RésidentLogementFoyer: vrai
      -- AccessionPropriétéLocalUsageExclusifHabitation:
        ménage.logement.résidence_principale
      -- SousLocataire: vrai
      -- LocationAccession: vrai # Justifié par L831-2, avec une
                                 # exception à venir
  conséquence rempli
```

######## Article L821-2 | LEGIARTI000038814974

Les aides personnelles au logement sont accordées au titre de
la résidence principale.

```catala
champ d'application ÉligibilitéAidesPersonnelleLogement:
  règle condition_logement_résidence_principale sous condition
    ménage.logement.résidence_principale
  conséquence rempli
```
"""


def test_parse_markdown():
    # Note that we deviate from the markdown spec as
    # 7 on more '#' signs are parsed as a markdown atx heading
    # (vanilla markdown has only up to 6 heading levels, mirroring
    # html)
    f = StringIO(catala_text)
    articles = parse_catala_file(f)
    assert len(articles) == 2
    ids = [article.id for article in articles]
    assert "LEGIARTI000038814944" in ids
    assert "LEGIARTI000038814974" in ids


def test_emit_markdown():
    md_parser = _make_markdown_parser()
    tok_list = md_parser.parse(catala_text)
    renderer = MDRenderer()
    md_result = renderer.render(tok_list, {"wrap": 80}, {})
    # Note that we deviate from the markdown spec as we may
    # emit more than 6 '#' characters for atx headings.
    assert "######## Article L821-2 | LEGIARTI000038814974" in md_result
