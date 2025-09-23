.. _legifrance:

==========================================
 Notes about Légifrance support in catleg
==========================================

 ``catleg`` is mostly a tool to support `catala <https://catala-lang.org>`__
 programming. Its features evolve from that need.

 Nevertheless, some features, especially fornatted Markdown output
 of law texts and articles, may be more generally useful.

 In the next section, we give an overview of the capabilities we support.

Querying Légifrance
===================

We support the following queries:

- Articles (``LEGIARTI``, ``JORFARTI``, ``CETATEXT``) from an identifier or URL.
- Code sections: a section of a code, with all subsections -- in French
  codes these will usually will be a

  - "Partie législative" or "Partie réglementaire", 
  - "Livre", 
  - "Titre", 
  - "Chapitre",
  - "Section", 
  - "Sous-section"
