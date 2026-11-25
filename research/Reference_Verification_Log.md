# Reference Verification Log

**Method.** Every DOI cited in the project was resolved against the Crossref REST API (`https://api.crossref.org/works/<DOI>`) on 2026-11-25. The table lists the metadata returned by Crossref (year | authors | title | journal | volume(issue) | pages). The APA 7 entries in `Literature_Review.md` and `backend/app/reports/references.py` were written to match these records.

Two references have no Crossref DOI record:

- **Holm (1979)**, *Scandinavian Journal of Statistics, 6*(2), 65–70 — published on JSTOR without a DOI (stable URL believed to be https://www.jstor.org/stable/4615733). **Action for students:** confirm via JSTOR before submission.
- **Logie (1995)**, *Visuo-spatial working memory*, Lawrence Erlbaum Associates — the original publisher/year is confirmed by a Crossref-indexed book review (Applied Cognitive Psychology, 1999, DOI 10.1002/(SICI)1099-0720(199902)13:1<89::AID-ACP564>3.0.CO;2-K). A 2014 Psychology Press reissue has DOI 10.4324/9781315804743.

## Crossref records

| DOI | Crossref metadata |
|---|---|
| 10.1006/cogp.1998.0684 | 1998 · Jolicœur, Pierre; Dell'Acqua, Roberto · The Demonstration of Short-Term Consolidation · Cognitive Psychology · v36(2) p138-202 |
| 10.1007/bf02289823 | 1959 · Greenhouse, Samuel W.; Geisser, Seymour · On Methods in the Analysis of Profile Data · Psychometrika · v24(2) p95-112 |
| 10.1016/0001-6918(90)90066-o | 1990 · Logie, Robert H.; Zucco, Gesualdo M.; Baddeley, Alan D. · Interference with visual short-term memory · Acta Psychologica · v75(1) p55-74 |
| 10.1016/0749-596x(89)90040-5 | 1989 · Turner, Marilyn L; Engle, Randall W · Is working memory capacity task dependent? · Journal of Memory and Language · v28(2) p127-154 |
| 10.1016/s0022-5371(80)90312-6 | 1980 · Daneman, Meredyth; Carpenter, Patricia A. · Individual differences in working memory and reading · Journal of Verbal Learning and Verbal Behavior · v19(4) p450-466 |
| 10.1016/s0028-3932(98)00159-6 | 1999 · Della Sala, Sergio; Gray, Colin; Baddeley, Alan; Allamano, Nadia; Wilson, Lindsey · Pattern span: a tool for unwelding visuo–spatial memory · Neuropsychologia · v37(10) p1189-1199 |
| 10.1016/s0079-7421(08)60452-1 | 1974 · Baddeley, Alan D.; Hitch, Graham · Working Memory · Psychology of Learning and Motivation · v() p47-89 |
| 10.1016/s1364-6613(00)01538-2 | 2000 · Baddeley, Alan · The episodic buffer: a new component of working memory? · Trends in Cognitive Sciences · v4(11) p417-423 |
| 10.1017/s0140525x01003922 | 2001 · Cowan, Nelson · The magical number 4 in short-term memory: A reconsideration of mental storage capacity · Behavioral and Brain Sciences · v24(1) p87-114 |
| 10.1037/0033-295x.103.3.403 | 1996 · Salthouse, Timothy A. · The processing-speed theory of adult age differences in cognition. · Psychological Review · v103(3) p403-428 |
| 10.1037/0096-1523.24.3.780 | 1998 · Awh, Edward; Jonides, John; Reuter-Lorenz, Patricia A. · Rehearsal in spatial working memory. · Journal of Experimental Psychology: Human Perception and Performance · v24(3) p780-790 |
| 10.1037/0096-1523.32.6.1436 | 2006 · Vogel, Edward K.; Woodman, Geoffrey F.; Luck, Steven J. · The time course of consolidation in visual working memory. · Journal of Experimental Psychology: Human Perception and Performance · v32(6) p1436-1451 |
| 10.1037/0096-3445.123.4.354 | 1994 · Conway, Andrew R. A.; Engle, Randall W. · Working memory and retrieval: A resource-dependent inhibition model. · Journal of Experimental Psychology: General · v123(4) p354-373 |
| 10.1037/0096-3445.125.1.4 | 1996 · Shah, Priti; Miyake, Akira · The separability of working memory resources for spatial thinking and language processing: An individual differences approach. · Journal of Experimental Psychology: General · v125(1) p4-27 |
| 10.1037/0096-3445.130.4.621 | 2001 · Miyake, Akira; Friedman, Naomi P.; Rettinger, David A.; Shah, Priti; Hegarty, Mary · How are visuospatial working memory, executive functioning, and spatial abilities related? A latent-variable analysis. · Journal of Experimental Psychology: General · v130(4) p621-640 |
| 10.1037/0096-3445.133.1.83 | 2004 · Barrouillet, Pierre; Bernardin, Sophie; Camos, Valérie · Time Constraints and Resource Sharing in Adults' Working Memory Spans. · Journal of Experimental Psychology: General · v133(1) p83-100 |
| 10.1037/0096-3445.133.2.189 | 2004 · Kane, Michael J.; Hambrick, David Z.; Tuholski, Stephen W.; Wilhelm, Oliver; Payne, Tabitha W.; Engle, Randall W. · The Generality of Working Memory Capacity: A Latent-Variable Approach to Verbal and Visuospatial Memory Span and Reasoning. · Journal of Experimental Psychology: General · v133(2) p189-217 |
| 10.1037/0096-3445.133.3.355 | 2004 · Klauer, Karl Christoph; Zhao, Zengmei · Double Dissociations in Visual and Spatial Short-Term Memory. · Journal of Experimental Psychology: General · v133(3) p355-381 |
| 10.1037/0278-7393.26.3.683 | 2000 · Jiang, Yuhong; Olson, Ingrid R.; Chun, Marvin M. · Organization of visual short-term memory. · Journal of Experimental Psychology: Learning, Memory, and Cognition · v26(3) p683-702 |
| 10.1037/bul0000046 | 2016 · Oberauer, Klaus; Farrell, Simon; Jarrold, Christopher; Lewandowsky, Stephan · What limits working memory capacity? · Psychological Bulletin · v142(7) p758-799 |
| 10.1038/36846 | 1997 · Luck, Steven J.; Vogel, Edward K. · The capacity of visual working memory for features and conjunctions · Nature · v390(6657) p279-281 |
| 10.1146/annurev-psych-120710-100422 | 2012 · Baddeley, Alan · Working Memory: Theories, Models, and Controversies · Annual Review of Psychology · v63(1) p1-29 |
| 10.1146/annurev.ne.13.030190.000325 | 1990 · Posner, Michael I.; Petersen, Steven E. · The Attention System of the Human Brain · Annual Review of Neuroscience · v13(1) p25-42 |
| 10.1162/089892902317361886 | 2002 · Fan, Jin; McCandliss, Bruce D.; Sommer, Tobias; Raz, Amir; Posner, Michael I. · Testing the Efficiency and Independence of Attentional Networks · Journal of Cognitive Neuroscience · v14(3) p340-347 |
| 10.1214/aoms/1177731915 | 1940 · Mauchly, John W. · Significance Test for Sphericity of a Normal $n$-Variate Distribution · The Annals of Mathematical Statistics · v11(2) p204-209 |
| 10.21105/joss.01026 | 2018 · Vallat, Raphael · Pingouin: statistics in Python · Journal of Open Source Software · v3(31) p1026 |
| 10.2466/11.it.3.1 | 2014 · Kerby, Dave S. · The Simple Difference Formula: An Approach to Teaching Nonparametric Correlation · Comprehensive Psychology · v3() p11.IT.3.1 |
| 10.3389/fnins.2014.00150 | 2014 · Heitz, Richard P. · The speed-accuracy tradeoff: history, physiology, methodology, and behavior · Frontiers in Neuroscience · v8() p |
| 10.3389/fpsyg.2013.00863 | 2013 · Lakens, Daniël · Calculating and reporting effect sizes to facilitate cumulative science: a practical primer for t-tests and ANOVAs · Frontiers in Psychology · v4() p |
| 10.3758/bf03192720 | 2005 · Unsworth, Nash; Heitz, Richard P.; Schrock, Josef C.; Engle, Randall W. · An automated version of the operation span task · Behavior Research Methods · v37(3) p498-505 |
| 10.3758/bf03193146 | 2007 · Faul, Franz; Erdfelder, Edgar; Lang, Albert-Georg; Buchner, Axel · G*Power 3: A flexible statistical power analysis program for the social, behavioral, and biomedical sciences · Behavior Research Methods · v39(2) p175-191 |
| 10.3758/bf03194326 | 2002 · Cocchini, Gianna; Logie, Robert H.; Sala, Sergio Della; MacPherson, Sarah E.; Baddeley, Alan D. · Concurrent performance of two memory tasks: Evidence for domain-specific working memory systems · Memory & Cognition · v30(7) p1086-1095 |
| 10.3758/bf03196573 | 2004 · Morey, Candice C.; Cowan, Nelson · When visual and verbal memories compete: Evidence of cross-domain limits in working memory · Psychonomic Bulletin & Review · v11(2) p296-301 |
| 10.3758/bf03196772 | 2005 · Conway, Andrew R. A.; Kane, Michael J.; Bunting, Michael F.; Hambrick, D. Zach; Wilhelm, Oliver; Engle, Randall W. · Working memory span tasks: A methodological review and user’s guide · Psychonomic Bulletin & Review · v12(5) p769-786 |
| 10.3758/bf03203619 | 1995 · Hautus, Michael J. · Corrections for extreme proportions and their biasing effects on estimated values ofd′ · Behavior Research Methods, Instruments, & Computers · v27(1) p46-51 |
| 10.3758/bf03203943 | 1974 · Phillips, W. A. · On the distinction between sensory storage and short-term visual memory · Perception & Psychophysics · v16(2) p283-290 |
| 10.3758/bf03207704 | 1999 · Stanislaw, Harold; Todorov, Natasha · Calculation of signal detection theory measures · Behavior Research Methods, Instruments, & Computers · v31(1) p137-149 |
| 10.3758/bf03210419 | 1988 · Pashler, Harold · Familiarity and visual change detection · Perception & Psychophysics · v44(4) p369-378 |
| 10.3758/s13423-011-0055-3 | 2011 · Rouder, Jeffrey N.; Morey, Richard D.; Morey, Candice C.; Cowan, Nelson · How to measure working memory capacity in the change detection paradigm · Psychonomic Bulletin & Review · v18(2) p324-330 |
| 10.3758/s13428-014-0458-y | 2015 · de Leeuw, Joshua R. · jsPsych: A JavaScript library for creating behavioral experiments in a Web browser · Behavior Research Methods · v47(1) p1-12 |
| 10.3758/s13428-018-01193-y | 2019 · Peirce, Jonathan; Gray, Jeremy R.; Simpson, Sol; MacAskill, Michael; Höchenberger, Richard; Sogo, Hiroyuki; Kastman, Erik; Lindeløv, Jonas Kristoffer · PsychoPy2: Experiments in behavior made easy · Behavior Research Methods · v51(1) p195-203 |
| 10.3758/s13428-020-01501-5 | 2021 · Anwyl-Irvine, Alexander; Dalmaijer, Edwin S.; Hodges, Nick; Evershed, Jo K. · Realistic precision and accuracy of online experiment platforms, web browsers, and devices · Behavior Research Methods · v53(4) p1407-1425 |
| 10.5334/pb-51-1-5 | 2011 · Bruyer, Raymond; Brysbaert, Marc · Combining Speed and Accuracy in Cognitive Psychology: Is the Inverse Efficiency Score (IES) a Better Dependent Variable than the Mean Reaction Time (RT) and the Percentage Of Errors (PE)? · Psychologica Belgica · v51(1) p5 |
| 10.7717/peerj.9414 | 2020 · Bridges, David; Pitiot, Alain; MacAskill, Michael R.; Peirce, Jonathan W. · The timing mega-study: comparing a range of experiment generators, both lab-based and online · PeerJ · v8() pe9414 |

## Fields not supplied by Crossref (check manually)

- Baddeley & Hitch (1974): Crossref gives pages 47–89 but no volume; the APA entry uses *Vol. 8* of *The Psychology of Learning and Motivation* (ed. G. H. Bower), which is the standard citation.
- Bruyer & Brysbaert (2011): Crossref gives first page 5 only; the APA entry uses pages 5–13.
- Lakens (2013) and Heitz (2014): Frontiers articles use article numbers (863 and 150) rather than page ranges.

No reference in this project was created without a verified source record. If you add references, verify them the same way:

```bash
curl -s "https://api.crossref.org/works/<DOI>" | python3 -m json.tool | less
```
