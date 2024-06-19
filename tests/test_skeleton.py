from io import StringIO

import pytest

from catleg.parse_catala_markdown import parse_catala_file
from catleg.query import _article_from_legifrance_reply
from catleg.skeleton import _article_skeleton, _formatted_article

from .test_legifrance_queries import _json_from_test_file


# Regression test for https://github.com/CatalaLang/catleg/issues/71
def test_no_article_renumbering():
    article_json = _json_from_test_file("LEGIARTI000044983201.json")
    article = _article_from_legifrance_reply(article_json)
    formatted_article_md = _formatted_article(article)
    assert "1. Le bénéfice ou revenu imposable est constitué" in formatted_article_md
    assert "2. Le revenu global net annuel" in formatted_article_md
    assert (
        "3. Le bénéfice ou revenu net de chacune des catégories" in formatted_article_md
    )


# Second regression test for https://github.com/CatalaLang/catleg/issues/71
# It would make sense to have this in test_catala_parsing.py but since
# there is another regression test for issue 71, let's group those cases here.
def test_no_article_renumbering_in_catala_file_parsing():
    text = """
######## Article 12 | LEGIARTI000006302214

L'impôt est dû chaque année à raison des bénéfices ou revenus que le
contribuable réalise ou dont il dispose au cours de la même année.

######## Article 13 | LEGIARTI000044983201

1. Le bénéfice ou revenu imposable est constitué par l'excédent du produit brut,
   y compris la valeur des profits et avantages en nature, sur les dépenses
   effectuées en vue de l'acquisition et de la conservation du revenu.

2. Le revenu global net annuel servant de base à l'impôt sur le revenu est
   déterminé en totalisant les bénéfices ou revenus nets mentionnés aux I à VI
   de la 1re sous-section de la présente section ainsi que les revenus, gains
   nets, profits, plus-values et créances pris en compte dans l'assiette de ce
   revenu global net en application des 3, 6 bis et 6 ter de l'article 158,
   compte tenu, le cas échéant, du montant des déficits visés au I de l'article
   156, des charges énumérées au II dudit article et de l'abattement prévu à
   l'article 157 bis.

```catala
champ d'application TraitementsSalairesDéclarant:
  définition revenu_brut_global égal à
    # Pensions, retraites, rentes avec abattement de droit commun article 158 5)
    # a) : attention, garder en synchronisation avec la liste l'article 79
    revenus.pensions_retraites_rentes
    + revenus.pensions_alimentaires_perçues
    + revenus.pensions_invalidité
    - abattement_pensions_retraites_rentes
    # Pensions, retraites, rentes sans abattement de droit commun article
    # 158 5) a) :
    + revenus.pensions_en_capital_plans_épargne_retraite
    # Traitements et salaire
    + traitements_salaires
    - déduction_frais_professionnels
champ d'application TraitementsSalairesFoyerFiscal:
  définition revenu_brut_global égal à
    (somme argent de résultats.revenu_brut_global pour résultats parmi
      déclarations_avec_résultats_traitements_salaires)
    + rentes_viagères_titre_onéreux
```

3. Le bénéfice ou revenu net de chacune des catégories de revenus visées au 2
   est déterminé distinctement suivant les règles propres à chacune d'elles.

Le résultat d'ensemble de chaque catégorie de revenus est obtenu en totalisant,
s'il y a lieu, le bénéfice ou revenu afférent à chacune des entreprises,
exploitations ou professions ressortissant à cette catégorie et déterminé dans
les conditions prévues pour cette dernière.

4. Pour l'application du 3, il est fait état, le cas échéant, du montant des
   bénéfices correspondant aux droits que le contribuable ou les membres du
   foyer fiscal désignés aux 1 et 3 de l'article 6 possèdent en tant qu'associés
   ou membres de sociétés ou groupements soumis au régime fiscal des sociétés de
   personnes mentionné à l'article 8.
    """
    articles = parse_catala_file(StringIO(text))
    article = next(elem for elem in articles if elem.id == "LEGIARTI000044983201")
    assert "1. Le bénéfice ou revenu imposable est constitué" in article.text
    assert "2. Le revenu global net annuel" in article.text
    assert "3. Le bénéfice ou revenu net de chacune des catégories" in article.text


@pytest.mark.parametrize("breadcrumbs", [False, True])
def test_article_skeleton(breadcrumbs: bool):
    article_json = _json_from_test_file("LEGIARTI000044983201.json")
    askel = _article_skeleton(article_json)
    assert "excédent du produit brut" in askel
    if breadcrumbs:
        assert "## Première Partie : Impôts d'État" in askel
