**Theme:** *Unlocking the Unseen Proteome — AI-driven clinical and market opportunity mapping for next-generation single-molecule protein diagnostics*

**Challenge partner:** Proteins.1 Oy, Helsinki
**Contact:** Prateek Singh, Founder & CEO — prateek@proteins1.com

---

## 0. How to use this document

You do **not** need a biology degree to win this challenge. You need to read a market carefully and argue well from evidence. Everything technical you need is explained here from first principles.

Figures in this brief are sourced inline. Where something is a company's claim about its own product, or a target rather than a demonstrated result, it is said so explicitly — and you should keep that distinction in your own work.


## 1. The challenge

> **How can we learn from proven leaders, so new innovators build on what works rather than reinvent everything?**

Proteins.1 has the science. What it wants from the sprint is **the map**.

The task is to study how the winners in life science and diagnostics actually reached the market, then turn that into a clear read on market trends and clinical opportunities for a breakthrough technology.

The knot to untie sits around data. There is a lot of it, the current way of looking at it is still taking shape, and the distance between deep tech and the customers who need it has to be closed with evidence rather than guesswork.

### Context

Deep tech and its customers often sit at opposite ends of the same problem. The science can run years ahead of anything on the market while the people who would benefit have no simple way to find it, trust it, or buy it. For a company like Proteins.1, the pressing questions are practical ones:

- **When does a technology stop being a research breakthrough and become a product?**
- **What did the companies that made it big actually do to get there?**
- **How should a young team read the data in front of it, so its answers are grounded rather than assumed?**

### The two strategic questions

Concretely, teams are asked to build an **AI-driven market and clinical opportunity map** that answers:

1. **Which specific disease areas and biomarker panels — principally in neurology and oncology — represent the strongest combination of clinical unmet need, technical feasibility, and market potential for a platform like this?**
2. **What actionable go-to-market strategy and translation pipeline would accelerate adoption from Research Use Only (RUO) to regulated in-vitro diagnostics (IVD) — and in what sequence?**

A serious answer to either one, deeply evidenced, beats a shallow answer to both.

---

## 2. What a strong case looks like

- **A usable market and clinical opportunity map** — not a broad essay on the industry.
- **A clear, repeatable way of looking at the data.** If we ran your method again next quarter on new inputs, would it produce a comparable answer? Show the method, not only the conclusion.
- **Named leaders, with what specifically made them succeed.** "They raised a lot" is not a finding. "They secured a reimbursement code before scaling their commercial team, which is why volume converted to revenue" is a finding.
- **Applications and routes to market where Proteins.1 has the most to gain** — pointed and prioritised.
- **Real use of AI** in collecting, structuring and interpreting the landscape, rather than AI as decoration.
- **Focused enough to act on.** Three defensible recommendations beat thirty observations.

A well-argued **outside view** and strong teamwork are what will set a case apart. You are encouraged to tell us something we do not want to hear, if you can evidence it.

### What will not score well

- A market-size slide ("the global proteomics market will reach $X billion by 2032") with no source discipline and no decision attached.
- A competitor grid copied from a market-research summary.
- Any number you cannot trace to a document.
- An AI-generated narrative with plausible but unverifiable specifics. **Fabricated precision is the fastest way to lose this jury.**

---

## 3. The challenge partner: Proteins.1

Proteins.1 is a Finnish deep-tech diagnostics company. It has built a physics-based, enzyme-free platform that amplifies and reads single protein molecules, detecting biomarkers across DNA, RNA and proteins from very small samples and at a sensitivity current instruments cannot reach.

The approach is often described as **doing for proteins what PCR did for DNA, without the enzymes** — with the aim of catching disease earlier and speeding up drug discovery. Early applications target **oncology, neurology and immunology** in research settings, with regulated clinical diagnostics to follow.

### Where the company stands today

- **Stage:** seed-stage, pre-commercial. The company describes itself as **technology developers — not yet an assay provider, a CRO, or a diagnostics company.** *Which of those it should become, and in what order, is close to the heart of this challenge.*
- **Funding:** ~€4.7M.
- **IP:** granted patents in the US and EU.
- **Validation:** the amplification principle has been reproduced for both DNA and protein targets at the **University of Catania** by Prof. Giuseppe Spoto, within an EU project.
- **Team:** founders with backgrounds in microfluidics, photonics and regulated medical devices, who have taken products to market before.


### Public footprint — start here

| Resource | Link |
|---|---|
| Company site | https://proteins1.com |
| VerSiLiB project | https://versilib.eu |
| CORDIS record | https://cordis.europa.eu/project/id/101046217 |
| Independent technology write-up | [State of the Future — *Detecting proteins in blood with photonics*](https://stateofthefuture.substack.com/p/detecting-proteins-in-blood-with) |
| Founder | [Prateek Singh, LinkedIn](https://www.linkedin.com/in/pratsku/) |

---

## 4. Technology deep dive

### 4.1 How AMT works

1. A target biomarker is captured on a **magnetic bead** by a high-affinity **permanent binder**.
2. A **variable magnetic field shuttles the bead** between a *storage side*, where it collects weakly-bound fluorescent **tracer** molecules, and an *active side* — a photonic/plasmonic **nanohole-array** readout surface.
3. On the active side the tracer is released and detected optically.
4. Because the bead cycles, **signal accumulates without enzymes**: the same molecule is effectively read again and again until certainty accumulates.

| Property | Commercial consequence |
|---|---|
| No enzymes | No cold chain, no polymerase error accumulation, simpler logistics and shelf life |
| Molecule-agnostic | Same chip reads protein, DNA, RNA — swap the binding chemistry |
| Cycling amplification | Sensitivity target beyond conventional digital-ELISA ceilings |
| Chip architecture | up to ~3.2 million functional units per well plate → high multiplexing and a rich per-sample data asset (~3.2M data points/sample) |
| Small sample | <100 µL per sample, enabling population-scale screening designs |

### 4.2 Enzymatic vs. physics-based amplification

| Feature | Enzymatic digital ELISA (e.g. Simoa) | Physics-based transport (Proteins.1 / AMT) |
|---|---|---|
| Amplification mechanism | Enzymatic turnover (β-galactosidase converting substrate to fluorescent product) | Magnetic bead-mediated tracer transport between storage and readout surfaces |
| Reagent stability | Enzymes degrade at room temperature; batch variation | No enzymes, no cold chain claimed |
| Error source | Enzymatic/polymerase error | No polymerase errors claimed |
| Multiplex capacity | Limited by spectral overlap (commercially ~4–10-plex) | Very high / "unlimited" multiplexing claimed via dense functional-unit arrays |
| Capital cost | High — specialised optical instrument | Positioned as lower-cost chip-based microfluidics |


### 4.3 Single-molecule counting statistics

Digital single-molecule assays use Poisson statistics to turn *the fraction of positive detection sites* into a concentration. For average occupancy λ per site, the probability of k molecules is:

$$P(k) = \frac{\lambda^k e^{-\lambda}}{k!}$$

When λ ≪ 1, the fraction of active sites approximates occupancy directly:

$$f_{\text{active}} = 1 - e^{-\lambda} \approx \lambda$$

And the practical limit of detection is set by background variability, not by the amplification itself:

$$\text{LOD} = \mu_{\text{blank}} + 3\sigma_{\text{blank}}$$

**Why this matters for the business case.** The mechanistic argument for an enzyme-free platform is that removing enzymatic turnover removes a major contributor to σ_blank, which lowers LOD. That is a *coherent hypothesis*, not a demonstrated result — and it is testable against published assay performance data. A team that tests it rather than asserting it will stand out.

### 4.4 The sensitivity ladder — with the arithmetic done correctly

$$1\ \text{aM} = 10^{-18}\ \text{mol/L} \times 6.022\times10^{23}\ \text{mol}^{-1} = 6.0\times10^{5}\ \text{molecules/L} \approx \mathbf{602\ \text{molecules per mL}}$$

Therefore, in a **100 µL** sample:

| Concentration | Molecules in 100 µL |
|---|---|
| 1 aM | **~60** |
| 10 aM | **~600** |
| 1 fM | **~60,000** |
| 1 pM | **~60,000,000** |

### 4.5 where the leading biomarkers actually sit

Take p-tau217, the flagship Alzheimer's blood biomarker, at a plasma level around 0.5 pg/mL, with tau at roughly 45 kDa:

$$\frac{0.5 \times 10^{-12}\ \text{g/mL} \times 10^{3}\ \text{mL/L}}{45{,}000\ \text{g/mol}} \approx 1.1\times10^{-14}\ \text{mol/L} \approx \mathbf{11\ fM}$$

**That is femtomolar, not attomolar** — roughly a thousand-fold above the attomolar frontier.

This is not a pedantic point. It reframes the entire commercial question, and it may be **the single most valuable analytical thread available to you in this sprint**:

- The neuro biomarkers that have already reached FDA clearance and reimbursement (p-tau217, Aβ42/40, NfL, GFAP) sit in a range where **femtomolar platforms already work**. Simoa, Lumipulse and NULISA got there first because that was enough.
- So **attomolar sensitivity is not automatically worth more money.** It is worth money only where a clinically valuable marker is *currently invisible* — too dilute, too early, or too masked to measure with what exists.
- Which means the real question is not "how sensitive can we get?" but **"which clinically decisive markers live below the current floor, and who would pay to see them?"**

Teams that identify specific markers in that band — and evidence why they matter clinically — will be doing precisely the work Proteins.1 needs and cannot easily do for itself.

### 4.6 The claims register

Carry this discipline into your deck. It is the difference between an analysis and a brochure.

| Claim | Status | Note |
|---|---|---|
| Enzyme-free amplification via affinity-mediated transport | **VERIFIED** | Patent FI20186055; EU-funded project; reproduced at University of Catania |
| Simultaneous protein + nucleic acid detection on one platform | **VERIFIED** | The EU project validated *BRAF* (DNA) and CSPG4 (protein) targets |
| ~3.2 million functional units per well plate | **VENDOR CLAIM** | From company materials. Physically consistent: at a sub-micron nanohole pitch, ~33,000 units per well is well within what array fabrication achieves |
| Single-molecule sensitivity | **ASPIRATION** | A target, not a published measured LOD — but a physically demonstrated regime. Simoa, NULISA and Voyager all operate there today |
| <100 µL sample volume | **ASPIRATION** | Conservative rather than heroic: Olink Flex already runs on 1 µL (§8.2). The constraint is not volume but how many target molecules that volume contains (§4.4) |
| Very high multiplexing | **ASPIRATION** | *Corrected from "unlimited."* Nothing is unlimited — multiplexing is bounded by the number of distinguishable addresses and by binder cross-reactivity. The defensible version of the claim is that this architecture is bounded by **spatial addressing** rather than by **spectral overlap**, which is what caps conventional fluorescence multiplexing at ~10-plex. That is a real and much stronger argument |
| Point-of-care deployment | **ASPIRATION** | Long-horizon vision, dependent on everything above landing first |
| Lower instrument cost than incumbents | **ASPIRATION** | Positioning, not a quoted price |
| **"1,000× more sensitive than ELISA"** | **CORRECTED** | This describes the incumbent, not an advance. Rissin et al. established in 2010 that single-molecule array (Simoa) detects serum proteins at **sub-femtomolar** concentrations versus conventional ELISA's picomolar floor — that *is* the ~1,000× step, and it happened sixteen years ago. Quoting it as a differentiator today concedes the argument. The comparisons that decide anything are against **Simoa, NULISA and Voyager** (§8.2). [Rissin et al., *Nature Biotechnology* (2010)](https://www.nature.com/articles/nbt.1641) |

**The constraint that binds all of these.** None of the aspirations above breaks physics — but one thing does limit every platform in this field, and the company says so itself: you cannot break the laws of chemistry. **Binding kinetics and diffusion** set a floor on how fast and how completely a target can be captured, no matter how good the readout is. At attomolar concentrations there may be only tens of molecules in the whole sample (§4.4), and getting each of them onto a bead is a mass-transport problem, not an optics problem. Any team arguing that sensitivity alone wins should read that constraint carefully — it is why "more sensitive" and "more useful" are not the same claim.

---

## 5. Why this is a hard commercial problem

**The technology is not the bottleneck. Adoption is.** A better measurement does not create a buyer. Between a working instrument and revenue sit: assay validation, clinical evidence, a regulatory pathway, a billing code, a guideline listing, and a laboratory willing to change a workflow it has run for twenty years.

### Two markets with opposite physics

| | Research / life sciences (RUO) | Clinical diagnostics |
|---|---|---|
| Market size | > €10B | > €100B |
| Regulation | Non-regulated (Research Use Only) | Heavily regulated (FDA / IVDR / CE) |
| Entry speed | Fast | Slow |
| Evidence needed | A convincing publication and a peer using it | Clinical trials, regulatory clearance, reimbursement |
| Reward | Modest, immediate | Large, delayed |
| Typical buyer | Academic core lab, pharma discovery group, CRO | Hospital lab, national screening programme, payer |

Almost every successful company in §9 **started in the fast, non-regulated market to fund and evidence the slow, regulated one**. The interesting question is *how they sequenced it* and how long they spent in each phase.

### Five shapes revenue can take

Choosing among these is a strategy decision, not a detail. Each has a different time-to-first-euro, gross margin, capital requirement and defensibility.

| # | Model | First revenue | Margin profile | Defensibility |
|---|---|---|---|---|
| 1 | **Instruments** (capital sale — the "razor") | Slow | Moderate | Low once copied |
| 2 | **Consumables / assay kits** (the "blades") | Follows instruments | High, recurring | Locked to installed base |
| 3 | **Services / CRO** (run samples for others) | **Fastest** | Moderate, labour-bound | Low, but builds data + relationships |
| 4 | **Data licensing** (sell cohort access to pharma) | Medium | Very high | Depends entirely on exclusivity |
| 5 | **Clinical testing** (LDT → reimbursed test) | Slowest | High at scale | Very high once coded and in guidelines |

**Mapping which of these Proteins.1 should pursue, in which order and why — evidenced by who did it before — is the core of this challenge.**

---

## 6. Domain primer — the 18 things you need to know

1. **Liquid biopsy** — testing blood (or urine, saliva, CSF) instead of cutting out tissue.
2. **Biomarker** — a measurable molecule whose level says something clinically useful.
3. **Assay** — the test procedure that measures a biomarker. A *platform* runs many assays.
4. **Plex / multiplexing** — how many biomarkers you measure from one sample at once. Higher plex usually lowers cost per data point but raises chemistry difficulty (cross-reactivity).
5. **Sensitivity ladder** — ng/mL (traditional ELISA) → pg/mL (multiplex bead assays) → fg/mL (digital ELISA) → single molecule. Each step opens biomarkers previously invisible in blood. See §4.4–4.5 for what this means in molecules.
6. **LOD / LLOQ** — Limit of Detection / Lower Limit of Quantification. The floor. **LOD is where you can say "something is there"; LLOQ is where you can say how much.** They are not the same and vendors sometimes quote whichever flatters.
7. **Dynamic range** — the span from lowest to highest measurable concentration, usually in logs. NfL needs wide range (asymptomatic baseline *and* acute spikes); a screening marker may not.
8. **cfDNA / ctDNA / cfRNA / EV** — cell-free DNA, circulating *tumour* DNA, cell-free RNA, extracellular vesicles.
9. **Proteomics** — measuring proteins at scale. More complex and more directly informative about *function* than the genome. Proteins.1's ground.
10. **Proteoform** — one gene can yield many distinct protein species (splice variants, phosphorylation, cleavage). Measuring "tau" and measuring *which tau* are different products with different value.
11. **MCED** — Multi-Cancer Early Detection. The field's biggest prize and biggest graveyard (§10).
12. **MRD** — Minimal/Molecular Residual Disease. Detecting whether cancer remains after treatment. Commercially the most successful liquid-biopsy category, because the clinical decision it informs is concrete.
13. **CDx (Companion Diagnostic)** — a test approved alongside a specific drug to select patients. **Pharma pays for these**, which is why they are a fast route to real money.
14. **RUO** — Research Use Only. Sellable without clearance, not for patient-care decisions.
15. **LDT** — Laboratory Developed Test. A test one certified lab develops and runs itself; historically a faster US route to market.
16. **CLIA / CAP / ISO 15189** — the accreditation regimes a clinical lab operates under. Relevant to the LDT phase.
17. **Reimbursement / CMS / MolDX / CLFS** — who actually pays. Medicare's Clinical Lab Fee Schedule sets a price; MolDX decides coverage for molecular tests. **A test with no reimbursement code is a science project.**
18. **Guideline inclusion** — when NCCN, ESMO or the American Cancer Society lists your test. Often the true inflection point for volume — **more than FDA clearance itself** (see Guardant in §9).

Plus: **IVDR** — the EU In Vitro Diagnostic Regulation; stricter and slower than its predecessor, and a genuine strategic variable for a European company deciding whether to launch in the EU or US first.

---

## 7. Target biomarker landscape

Proteins.1's disease-area priorities are oncology, neurology and immunology in research settings first, regulated diagnostics to follow. Treat the following as **starting scope**, then use the frame in §14 to prioritise.

### 7.1 Neurology / neurodegeneration

The commercially hottest segment right now — and, per §4.5, the one where **femtomolar platforms already suffice**, which is itself the strategic puzzle.

| Marker | Clinical relevance | Notes |
|---|---|---|
| **p-tau217** (also p-tau181, p-tau231) | Strongest plasma correlate of amyloid and tau pathology, years before cognitive decline | Now FDA-cleared in a plasma ratio test (§9). ~10 fM range |
| **NfL** (neurofilament light) | Axonal damage across MS, ALS, AD, TBI | Needs wide dynamic range, not just low LOD |
| **GFAP** | Reactive astrogliosis, early neuroinflammation | Complements p-tau prognostically |
| **Aβ42/40 ratio** | Reduced plasma ratio indicates brain amyloid | Component of the cleared Lumipulse ratio test |
| **UCH-L1, BD-tau** | Neuronal injury; brain-derived tau specificity | Less commoditised |
| **α-synuclein seeds/oligomers** | Hallmark of Parkinson's and Lewy body dementia | Seed amplification assays validated in the PPMI cohort — [*Lancet Neurology* 2023](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(23)00109-6/abstract), [longitudinal kinetics 2025](https://www.thelancet.com/journals/laneur/article/PIIS1474-4422(25)00157-7/fulltext). Note this is an *amplification* assay, conceptually adjacent to what AMT does — worth understanding |

### 7.2 Oncology

| Marker class | Clinical relevance |
|---|---|
| CA-125 (MUC16), HE4 | Ovarian cancer; established but limited early-stage sensitivity |
| AFP, AFP-L3%, PIVKA-II (DCP) | Hepatocellular carcinoma surveillance |
| GDF-15 | Broad prognostic marker |
| CEA, PSA, CA19-9 at ultra-low abundance | Legacy markers whose early-stage utility is limited by *assay* sensitivity, not biology — a direct test of the platform thesis |
| Exosomal surface proteins (EpCAM, CD63, PD-L1) | Tumour-derived vesicle signatures; immune evasion and metastatic potential |
| Protein + ctDNA co-detection | The multiomic argument — CancerSEEK's original premise (§9) |

### 7.3 Renal / inflammation and cytokines

- **Renal:** KIM-1, NGAL, Cystatin C — established clinical need, high volumes, competitive.
- **Cytokines/immunology:** IL-1β, IL-6, IL-8, IL-17A, IFN-γ, CXCL10 (IP-10), TRAIL — dominated by multiplex incumbents (Bio-Plex, MSD, Olink); a pricing and plex battleground rather than a sensitivity one.

### 7.4 Blue ocean: the worked example worth studying closely

Two targets have no clear commercial incumbent:

- **Free IL-18** (as distinct from the IL-18BP-bound fraction) — measuring the *free* fraction requires discrimination that standard immunoassays do not provide.
- **LINE-1 ORF1p** — a retrotransposon-encoded protein re-expressed across many high-mortality cancers while largely absent from healthy adult tissue.

**ORF1p is the single best case study in this brief**, and every team should read it:

> Researchers at Mass General Brigham and the Wyss Institute showed that ORF1p is detectable in blood **only because an ultrasensitive single-molecule assay (Simoa) made it visible** — it sits below the floor of conventional immunoassays. It behaves as a specific multi-cancer signal, and it was essentially invisible as a blood biomarker until the sensitivity existed to see it.
>
> [*Cancer Discovery* (2023) — Ultrasensitive Detection of Circulating LINE-1 ORF1p as a Specific Multicancer Biomarker](https://aacrjournals.org/cancerdiscovery/article/13/12/2532/731592/Ultrasensitive-Detection-of-Circulating-LINE-1) · [Mass General Brigham release](https://www.massgeneralbrigham.org/en/about/newsroom/press-releases/ultrasensitive-blood-test-detects-pan-cancer-biomarker) · [Wyss Institute](https://wyss.harvard.edu/news/ultrasensitive-blood-test-detects-pan-cancer-biomarker)

This is the Proteins.1 thesis in one published example: **a sensitivity jump did not improve an existing test — it created a biomarker that did not previously exist commercially.** Ask what *else* is sitting below the current floor, and build your case around that logic rather than around incremental improvement.

> **Note on scope.** Proteins.1's exact prioritised target list is confidential and is not distributed. Work at the level of the **marker class** — which is where the market analysis lives anyway, and which keeps your conclusions usable even as the panel evolves.

---

## 8. Competitive landscape

### 8.1 The four eras

| Era | Period | Representative players | Sensitivity | Plex |
|---|---|---|---|---|
| Traditional | 1970–1990 | ELISA/RIA, Fujirebio | ng/mL | Single analyte |
| First digital | 1990–2000 | Luminex (DiaSorin), MSD | pg/mL | 10–500 |
| Ultra-sensitive | 2000–2020 | Quanterix (Simoa), Olink (PEA) | fg/mL | 10 – 5,400 |
| Single-molecule | 2025– | Nautilus, Proteins.1 | single molecule (claimed) | high / "unlimited" (claimed) |

### 8.2 Verified platform specifications

Use these rather than remembered numbers. All figures are the vendors' own published specs — **VENDOR CLAIM** by definition, but published and checkable.

| Platform | Company | Mechanism | Plex | Sample vol. | Source |
|---|---|---|---|---|---|
| **Simoa** | Quanterix | Bead + femtolitre-well digital ELISA (enzymatic) | ~4–10-plex commercial | — | [quanterix.com](https://www.quanterix.com/) |
| **Explore HT** | Olink (Thermo Fisher) | Proximity Extension Assay + NGS readout | **5,400+ proteins** | **2 µL** | [Olink product comparison](https://olink.com/products/compare) |
| **Reveal** | Olink | PEA | 1,000+ assays | 4 µL | same |
| **Flex** | Olink | PEA | ~200 pre-validated | 1 µL | same |
| **NULISA / ARGO HT** | Alamar Biosciences | Nucleic-acid-linked immunoassay + sequencing readout | 200–5,000-plex class; Inflammation Panel 250 launched | — | [*Nature Communications* (2023) — attomolar sensitivity, peer-reviewed](https://www.nature.com/articles/s41467-023-42834-x) · [ARGO HT launch](https://alamarbio.com/alamar-biosciences-announces-commercial-launch-of-the-argo-ht-system-and-the-nulisaseq-inflammation-panel-250-for-ultra-high-sensitivity-protein-analysis-in-biofluids/) |
| **Voyager** | Nautilus Biotechnology (NASDAQ: NAUT) | "Iterative Mapping" — probes single molecules over tens–hundreds of cycles on ultra-dense nanoarrays | **up to 10 billion intact proteins/proteoforms per run** | — | [Unveiled at US HUPO, Feb 2026](https://investors.nautilus.bio/news-releases/news-release-details/nautilus-biotechnology-unveils-voyager-platform-enabling-single) |

**Note the Alamar data point carefully.** NULISA's attomolar sensitivity is published in *Nature Communications* — peer-reviewed, not a marketing claim. **The attomolar frontier already has a commercial occupant with a shipping instrument and a public market listing.** Any Proteins.1 positioning built on "we are the only ones who can reach attomolar" is wrong. The differentiation argument has to be something else — enzyme-free chemistry, cost per data point, multiomic capability on one chip, sample volume, or workflow. Working out *which* is a genuinely useful deliverable.

### 8.3 The closest direct competitor: Nautilus

Nautilus is the nearest analogue to Proteins.1's single-molecule, high-density-array architecture, and it is **roughly 12 months ahead commercially**:

- Voyager platform unveiled at **US HUPO, February 2026**; measures up to 10 billion intact proteins and proteoforms per run.
- First evaluation unit **installed at the Buck Institute for Research on Aging**, generating reproducible **tau proteoform** data — external validation by a credible third party.
- **Early Access Program launched January 2026**, starting with a **Tau Proteoforms assay** quantifying up to 768 full-length tau proteoform groups, run as fee-for-service.
- **Commercial availability expected to initiate in late 2026.**

Study this sequence closely — it is a live, documented, near-real-time example of exactly the RUO→commercial translation Proteins.1 is asking you to map: *unveil at the field's flagship conference → place an instrument at a marquee institute → generate third-party data → open fee-for-service early access on a single high-value assay → full launch.* Note also that they entered on **tau proteoforms** — the neurology beachhead — and that fee-for-service (revenue model #3) came before instrument sales (#1).

### 8.4 Other companies worth mapping

**Ultra-sensitive & high-plex proteomics:** Quanterix · Olink (Thermo Fisher) · SomaLogic (Illumina) · Alamar · Nautilus · Nomic Bio · Seer · Standard BioTools · Meso Scale Discovery · Bio-Rad · Luminex/DiaSorin

**Liquid biopsy & screening:** Guardant Health · Natera · Exact Sciences (Abbott) · GRAIL · Freenome · DELFI · Harbinger Health · Nucleix · Foundation Medicine (Roche) · Personalis · Adela

**Neuro diagnostics:** C2N Diagnostics · Fujirebio · ALZpath · Roche Diagnostics · Labcorp

**Nordic / Finnish ecosystem** — the accessible network, and under-analysed: Nightingale Health · Genomill · Uniogen · Medix Biochemica · HyTest · Hidex · Aidian · Labsystems Diagnostics · Biohit · Elypta (SE) · Immunovia (SE) · Reccan (SE) · SAGA Diagnostics (SE) · Hedera Dx (CH/FI)

**On Guardant and Natera as "competitors":** they are ctDNA/genomic comparators, not direct protein-detection rivals. The strategic argument for protein over ctDNA in early-stage disease is often asserted loosely; here is the quantitative version, which is much more useful.

A Stanford model of ctDNA shedding calibrated on 176 non-small-cell lung cancer patients estimated a mean shedding probability of **1.4 × 10⁻⁴ genome equivalents per cell death**. The consequence is stark: at a **1 cm³ tumour**, a standard **15 mL blood draw** contains on the order of **1.5 ctDNA genome equivalents** — a tumour fraction of about **0.02%**. The model put median detection size for annual lung screening at 2.0–2.3 cm.

**That is a counting problem, not an assay-sensitivity problem.** You cannot detect what is not in the tube, and no improvement in sequencing depth conjures more copies. Protein biomarkers are not subject to the same limit — a secreted or shed protein can be present in far higher copy number than the tumour's DNA, which is the real basis for the "proteins arrive earlier" argument.

**This is the strongest single argument available for the whole platform, so make it properly** — with these numbers, this citation, and the marker-specific evidence that a given protein actually is elevated at stage I. Asserted without that, it is marketing; evidenced, it is a thesis.

Source: [Avanzini et al., *A mathematical model of ctDNA shedding predicts tumor detection size*, **Science Advances** 6(50):eabc4308 (2020)](https://www.science.org/doi/10.1126/sciadv.abc4308) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/33310847/) · [GenomeWeb summary](https://www.genomeweb.com/cancer/stanford-team-develops-mathematical-model-ctdna-shedding-predict-lung-cancer-tumor-size)

---

## 9. Historical leader benchmarks: how winners actually reached the market

This answers the founder's question directly. Read it as a set of *strategies*, not a scoreboard. The "years to deal" column is revealing: it varies by more than an order of magnitude, and the variation is not random.

| Company (founded) | Defining commercial event | Structure | Yrs | Status |
|---|---|---|---|---|
| **Thrive Earlier Detection** (2018) | Acquired by Exact Sciences, Oct 2020, **up to $2.15B** (~$1.7B upfront + $450M milestones) — **while pre-commercial**, on the CancerSEEK protein+DNA panel | M&A pre-revenue | **2** | [Verified](https://www.goodwinlaw.com/en/news-and-events/news/2020/10/10_27-thrive-earlier-detection-to-be-acquired) |
| **Alamar Biosciences** (2020) | **$128M Series C** (Feb 2024, Sands Capital); **IPO 17 Apr 2026 at $17.00/share on Nasdaq (ALMR), ~$191M gross** | Venture → IPO | **~4–6** | [Series C](https://alamarbio.com/alamar-biosciences-raises-128-million-in-oversubscribed-series-c-financing-to-accelerate-commercialization-of-its-proteomics-platform/) · [IPO pricing](https://alamarbio.com/alamar-biosciences-announces-pricing-of-upsized-initial-public-offering/) |
| **Olink Proteomics** (2016) | UK Biobank Pharma Proteomics Project with 14 pharma co-sponsors; **acquired by Thermo Fisher for $3.1B (2024)**; platform selected for UKB's 500k-participant expansion (2025) | Consortium data → M&A | **~5** | [Thermo Fisher](https://ir.thermofisher.com/investors/news-events/news/news-details/2024/Thermo-Fisher-Scientific-Completes-Acquisition-of-Olink-Announces-Commencement-of-Subsequent-Offering-Period/default.aspx) · [UKB expansion](https://ir.thermofisher.com/investors/news-events/news/news-details/2025/Thermo-Fisher-Scientifics-Olink-Platform-Selected-for-Worlds-Largest-Human-Proteome-Study/default.aspx) |
| **Foundation Medicine** (2010) | Roche took a **majority stake, completed 7 April 2015**: ~$250M gross proceeds to FMI (tender offer plus 5M newly issued shares at $50/share), a broad R&D collaboration with **potential for >$150M in Roche funding**, and ex-US distribution rights — roughly **$1.03B** total Roche outlay for the stake. Roche acquired the remainder in 2018 | Equity + CDx co-dev + distribution | **~5** | [FMI/Roche completion release](https://www.foundationmedicine.com/press-releases/foundation-medicine-and-roche-complete-strategic-transaction-to-advance-molecular-information-and-precision-medicine-in-oncology) · [Fierce Biotech](https://www.fiercebiotech.com/medical-devices/roche-grabs-majority-share-foundation-medicine-for-1b-plus-milestones) |
| **C2N Diagnostics** (2017) | PrecivityAD / AD2 plasma amyloid tests; **Eisai investment of up to $15M, announced March 2024**, alongside a collaboration to broaden access to blood-based Alzheimer's testing | Strategic equity + commercial collaboration | **~7** | [C2N announcement](https://c2n.com/news-releases/cn-diagnostics-llc-announces-investment-from-eisai-inc) · [Eisai release](https://www.eisai.com/news/2024/news202414.html) |
| **Guardant Health** (2012) | **Shield** — [first FDA-approved blood test for primary CRC screening, July 2024](https://investors.guardanthealth.com/press-releases/press-releases/2024/Guardant-Healths-Shield-Blood-Test-Approved-by-FDA-as-a-Primary-Screening-Option-Clearing-Path-for-Medicare-Reimbursement-and-a-New-Era-of-Colorectal-Cancer-Screening/default.aspx); **NCCN guidelines 2025**; **American Cancer Society guidelines May 2026**; UnitedHealth coverage 2026 | LDT → FDA → guidelines → coverage | **~12** | [ACS inclusion](https://investors.guardanthealth.com/press-releases/press-releases/2026/American-Cancer-Society-Recommends-Guardant-Healths-Shield-Blood-Test-in-Updated-Colorectal-Cancer-Screening-Guidelines/default.aspx). **Correction:** a "$100M AstraZeneca partnership" circulates in secondary summaries and is not supported. The real relationship is a [Dec 2018 CDx partnership for Tagrisso and Imfinzi](https://investors.guardanthealth.com/press-releases/press-releases/2018/Guardant-Health-Partners-with-AstraZeneca-to-Develop-Blood-Based-Companion-Diagnostic-Tests-for-Tagrisso-and-Imfinzi/default.aspx) and a [2022 ESR1 breast-cancer CDx collaboration](https://investors.guardanthealth.com/press-releases/press-releases/2022/Guardant-Health-Announces-Collaboration-With-AstraZeneca-to-Develop-Companion-Diagnostic-to-Identify-Patients-With-ESR1-mutated-Metastatic-Breast-Cancer/default.aspx) — **financial terms undisclosed in both** |
| **Nightingale Health** 🇫🇮 (2013) | **UK Biobank: 500,000 blood samples** by NMR metabolomics; results released to researchers globally; pharma consortium funding | Data licence per partner | **~9** | [UK Biobank](https://www.ukbiobank.ac.uk/news/nightingale-health-and-uk-biobank-announces-major-initiative-to-analyse-half-a-million-blood-samples-to-facilitate-global-medical-research/) |
| **Quanterix** (2007) | Simoa; IPO 2017; Accelerator CRO services; **CMS set $897 for the LucentAD Alzheimer's test (Sept 2025)**; acquired **Akoya Biosciences (2025, ~$127M)** | Instruments + consumables + CRO → reimbursed test | **~11** | [CMS price](https://seekingalpha.com/news/4493764-quanterix-rises-on-cms-price-for-lucentad-alzheimer-blood-biomarker-test) · [Akoya](https://ir.quanterix.com/news-releases/news-release-details/quanterix-completes-acquisition-akoya-biosciences-creating-first) |
| **Natera (Signatera)** (2004) | ctDNA MRD; **Medicare coverage via MolDX**. **FY2025: revenue $2,306.1M, +35.9% YoY; gross margin 64.7%; 3,525,500 tests processed**, of which ~800,800 oncology tests (+51.6%) | LDT → MolDX LCD → reimbursement | **~14** | [Natera FY2025 results](https://investor.natera.com/news/news-details/2026/Natera-Reports-Fourth-Quarter-and-Full-Year-2025-Financial-Results/). **Correction:** a "~$2,900 Signatera ASP" circulates in secondary sources; Natera does **not** disclose per-product ASP, so treat any such figure as an estimate, not a reported number |
| **SomaLogic** (1999) | SomaScan 7,000-plex; merged into Standard BioTools 2024; **assets sold to Illumina for up to $425M** ($350M cash + up to $75M milestones), 2026 | Data licence + milestones → asset sale | **20+** | [GenomeWeb](https://www.genomeweb.com/sequencing/illumina-acquire-somalogic-assets-standard-biotools-425m) |
| **Exact Sciences** (1995) | Cologuard; acquired Thrive and Base Genomics; **acquired by Abbott for ~$21B, closed 23 March 2026** | Screening franchise → strategic exit | **~31** | [Abbott](https://abbott.mediaroom.com/2026-03-20-Abbott-acquisition-of-Exact-Sciences-set-to-close-on-March-23,-2026) |
| **Fujirebio** | **First FDA-cleared blood test for Alzheimer's diagnosis** — Lumipulse G pTau217/β-amyloid 1-42 plasma ratio, May 2025; launched via Labcorp | IVD clearance → lab channel | — | [FDA](https://www.fda.gov/news-events/press-announcements/fda-clears-first-blood-test-used-diagnosing-alzheimers-disease) |

### The pattern hypotheses — stress-test these, don't accept them

**Proteins.1's current internal read:**
> The fastest paths to large deal values are driven by a **sensitivity or platform advantage competitors cannot replicate, combined with outcomes-linked cohort data**. Data-licence deals without exclusivity or outcomes linkage plateau at low single-digit millions per partner. Strategic equity + CDx deals deliver the highest per-indication value, but require the pharma partner to have an active programme in that indication.

**A second reading worth testing:** the fastest deals (2–5 years) were M&A or large pre-commercial data partnerships anchored to **a landmark validation cohort plus a single strategic partner** (Thrive, Foundation Medicine, Olink). Reimbursement-driven clinical adoption (Natera, Quanterix, Guardant) took over a decade but built durable recurring revenue. As a pre-commercial deep-tech platform, Proteins.1 most closely resembles the **Thrive / Olink** starting position — implying its fastest realistic path to a milestone runs through **a landmark cohort plus a strategic partner**, not direct clinical reimbursement.

**Your job is to break, confirm, or refine both.** Does either survive contact with §10? What does each miss?

---

## 10. The control group: what going wrong looks like

Analysis of winners without a control group is survivorship bias, and the jury will notice.

### GRAIL / NHS-Galleri — February 2026

The best-funded MCED programme in the world **missed its primary endpoint**: no statistically significant reduction in stage III/IV cancers, despite a favourable trend in a pre-specified group and a meaningful reduction in stage IV diagnoses. Shares fell ~50% in a day.

[MedTech Dive](https://www.medtechdive.com/news/grails-multi-cancer-early-detection-test-misses-study-goal/812736/) · [GRAIL's own framing of the same trial](https://grail.com/press-releases/landmark-nhs-galleri-trial-demonstrates-a-substantial-reduction-in-stage-iv-cancer-diagnoses-increased-stage-i-and-ii-detection-of-deadly-cancers-and-four-fold-higher-cancer-detection-rate/)

**Read both.** The same trial, narrated two ways, is a free lesson in evidence interpretation — and in how a challenge like this one gets answered dishonestly. Lesson to interrogate: **capital and sensitivity do not substitute for a clinical endpoint a payer will pay for.**

### The Quanterix paradox

The closest technical comparable to Proteins.1's sensitivity claim — yet roughly flat revenue and a distressed valuation, even while holding a reimbursed Alzheimer's test and having acquired Akoya. **Why does a genuine sensitivity lead not convert into growth?**

This is arguably **the most important single question in this brief.** If a team answers it convincingly, everything else in the strategy follows.

### The Theranos shadow

Any ultra-sensitive, small-sample, "one drop of blood" claim inherits a credibility discount. How do credible companies signal the difference? (Note how Nautilus did it: third-party instrument placement, reproducible data from an independent institute, peer-reviewed publication, staged access.)

---

## 11. Commercial translation pathway

| Phase | Target customer | Objective | Regulatory barrier | Revenue model (§5) |
|---|---|---|---|---|
| **1. RUO** | Pharma R&D, academic core labs, biobanks (FinnGen, UK Biobank) | Target validation, trial biomarker stratification, publications | Fast deployment; no IVD clearance needed | #3 services, then #1/#2 |
| **2. LDT** | Central reference labs, specialised diagnostic clinics | Clinical service under CLIA / CAP / ISO 15189 | Moderate validation | #5 (early) |
| **3. IVD** | Primary care, hospital pathology labs, screening programmes | Mass-market screening and diagnostic kits | FDA 510(k)/PMA (US); EU IVDR 2017/746 | #5 at scale, #2 recurring |

### Target customer personas

Use these to anchor sizing and any interviews you conduct during the sprint.

1. **Biopharma translational-medicine director** — needs sensitive pharmacodynamic and target-engagement biomarkers for phase I–III neurology and oncology trials. *Has budget now. Buys services, not instruments. Cares about turnaround and data quality, not regulatory status.*
2. **Biobank / cohort principal investigator** — needs low-sample-volume, multi-omic characterisation of longitudinal cohorts. *Sample volume is often the binding constraint — note Olink Flex runs on 1 µL. Access to a landmark cohort is the strategic prize (see Olink and Nightingale in §9).*
3. **Clinical pathologist / oncologist** — needs high-throughput, low-cost early-detection assays with rapid turnaround. *Cannot buy until reimbursement and guidelines exist. The slowest but largest customer.*
4. **CRO / central lab** — buys capacity and menu breadth. *An under-considered channel: it converts an instrument sale into a volume relationship without requiring clinical evidence.*

---

## 12. Pricing anchors and unit economics

Public catalogue prices are a legitimate and underused source. These are list prices from vendor materials — real, checkable, and enough to derive cost-per-data-point at different plex levels.

| Reference | Price | Source type |
|---|---|---|
| Bio-Plex Pro Human Cytokine Screening Panel, 48-plex (96-well) | €9,141 (≈ €95/well) | Bio-Rad catalogue |
| Bio-Plex Pro Human Inflammation Panel 1, 37-plex | €7,089 | Bio-Rad catalogue |
| Bio-Plex Pro TNF-α singleplex set | €307 (+ separate reagent kit) | Bio-Rad catalogue |
| [ProcartaPlex Human Immune Response Panel, 80-plex, 96 tests](https://www.thermofisher.com/order/catalog/product/EPX800-10080-901) | ~€13,000 | Thermo Fisher catalogue |
| [ProQuantum high-sensitivity immunoassay kit, 96 tests](https://www.thermofisher.com/fi/en/home/life-science/antibodies/immunoassays/proquantum-high-sensitivity-immunoassays.html) | ~€600 | Thermo Fisher catalogue |
| Ultrasensitive neurology kits, 96 tests | ~€1,000 | Taudia |
| Empty 384/1536-well plates | €6–20/plate | Revvity catalogue |
| High-volume single-plex reagent-only cost | as low as ~€0.025/data point | Revvity catalogue |
| xMAP/MAGPIX vs. ELISA reagent cost per 96-well plate | €23.75 vs €56.00 | NMI Tübingen benchmark |
| **Quanterix LucentAD multi-marker AD panel** | **$897/test** (CMS, Sept 2025) | Medicare CLFS |

**The derivation that matters.** A 48-plex kit at €9,141 for 96 wells implies **~€95/well in raw kit cost** before labour, instrument amortisation and margin. Meanwhile bulk single-plex reagent cost can reach cents per data point. **The spread between those two numbers is where the entire pricing strategy lives** — and it depends heavily on how many samples actually run per kit in practice, which vendors do not advertise. Nailing this down for two or three vendors would be a genuinely valuable output.

### The company's own working GTM hypothesis — for you to stress-test

Shared deliberately so you have something concrete to attack rather than a blank page. **These are internal working assumptions, not validated plans.**

- Year 1–2: in-house proof of concept
- Year 2–3: CRO-style service revenue (order of ~100k samples at ~€100/sample)
- Year 3–5: first instrument installations at customer sites
- Long-run reference point: Quanterix-scale deployment (~1,000 installed instruments, ~1,500 plates per instrument per year)

**Questions worth asking of it:** Is ~100k samples in year 2–3 achievable for a pre-commercial platform — what did Alamar or Nautilus actually do in their equivalent year? Is €100/sample consistent with the catalogue anchors above? Does the instrument-installation model fit a market where Olink's own growth came through *service* providers rather than placed boxes?

---

## 13. Regulatory reality check

- **US:** FDA 510(k) (substantial equivalence to a predicate) is faster than PMA (full premarket approval). The **LDT route** historically bypassed both, but its regulatory status has been contested — check the current position rather than assuming.
- **EU:** IVDR 2017/746 replaced IVDD with substantially higher evidence and notified-body requirements. For a European startup this is a real strategic fork: **many EU companies now pursue the US first.** Whether Proteins.1 should is a live question worth an evidenced answer.
- **The sequence that actually produces revenue** — visible in the Guardant row of §9 — is: clearance → guideline inclusion → payer coverage. Each takes time and each can fail independently. **FDA approval alone did not make Shield a business; ACS and NCCN inclusion plus UnitedHealth coverage did.**

---

## 14. Building the map

### 14.1 The scoring frame — eight dimensions

For any candidate opportunity — a *(disease area × marker class × customer segment × revenue model)* combination — score:

| Dimension | Question | Evidence you can actually find |
|---|---|---|
| **1. Unmet measurement need** | Can incumbents measure this at the concentration that matters? | Vendor LoD/LLOQ specs; publications reporting "below detection limit" |
| **2. Clinical decision attached** | Does the result change what a clinician does? | Guidelines (NCCN, ESMO, ACS); drug labels; trial endpoints |
| **3. Payer path exists** | Is there a code, a price, a precedent? | CMS CLFS; MolDX LCDs; national reimbursement lists |
| **4. Evidence cost** | How many samples, years, euros to prove it? | Cohort sizes in comparable pivotal studies (ClinicalTrials.gov) |
| **5. Sample access** | Can you get the biobanked samples to do it? | Biobank catalogues, consortium membership, published access terms |
| **6. Incumbent intensity** | How many vendors already sell this? | Cross-vendor catalogue overlap |
| **7. Time to first revenue** | Which revenue model fits, how fast? | Comparable companies' first-revenue dates |
| **8. Defensibility** | What stops a competitor copying it in 18 months? | Patent families; exclusivity terms in comparable deals |

Two derived views are worth building:

- **Commoditised vs. blue-ocean.** Markers available off-the-shelf from 2+ vendors → compete on price and plex. Specialty singleplex only → premium opportunity. No commercial equivalent → blue ocean, but you must prove the clinical need yourself (the ORF1p pattern, §7.4).
- **Sequence, not choice.** The output should be an ordered path — *"do A in year 1 to fund B in year 3, because company X did exactly this"* — not a ranked list of independent options.

### 14.2 A workable AI pipeline

```
┌──────────────────────────────────────────────────────────────┐
│ LAYER 1 — Ingestion & mining (NLP / LLM)                     │
│ openFDA 510(k)/PMA, ClinicalTrials.gov v2 API, SEC EDGAR,    │
│ CMS CLFS, CORDIS, PubMed, exhibitor directories (§16)        │
│ → extract: trial phase, cohort size, endpoint, sponsor,      │
│   biomarker, price, deal terms  ·  KEEP THE SOURCE URL       │
└──────────────────────────────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 2 — Knowledge graph                                    │
│ protein → disease → tissue specificity → plasma abundance    │
│ → assay availability → vendor → price                        │
│ Cross-reference Human Protein Atlas, UniProt, cohort data    │
└──────────────────────────────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 3 — Scoring engine                                     │
│ Composite Opportunity Index per (marker × segment × model)   │
│ Weights explicit and adjustable — no black boxes             │
└──────────────────────────────────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ LAYER 4 — Output                                             │
│ Clinical impact × commercial feasibility 2×2, plus a         │
│ SEQUENCED go-to-market recommendation with evidence links    │
└──────────────────────────────────────────────────────────────┘
```

### 14.3 A transparent Opportunity Index

$$OI_i = w_1 U_i + w_2 \Delta S_i + w_3 M_i - w_4 R_i$$

where, each scored 0–10:

- **U** — unmet clinical need (mortality, late-stage diagnosis rate, current diagnostic delay)
- **ΔS** — analytical sensitivity gain vs. the legacy assay LOD for that marker *(this is where §4.5 bites: for many neuro markers ΔS is near zero, because femtomolar already suffices)*
- **M** — addressable market (annual test volume × realistic price)
- **R** — regulatory and clinical validation burden
- **w₁…w₄** — user-defined weights summing to 1

Making the weights explicit is the point: it lets the jury interrogate your *judgement* rather than your arithmetic, and it makes the method repeatable. **Show a sensitivity analysis** — which recommendations survive when you change the weights? Ones that flip under small weight changes are not recommendations, they are noise.

**Tooling:** `requests` / `BeautifulSoup` / `BioPython` or LLM function-calling for extraction · `pandas` for the entity work · `NetworkX` or `Neo4j` for the graph · `Streamlit`, `Plotly` or `Dash` for the dashboard.

---

## 15. Using AI well on this challenge

### Where AI genuinely wins here

- **Building a company census from scratch.** Pull an exhibitor directory or a regulatory database (§16), normalise the technology and sub-sector labels into a consistent taxonomy, de-duplicate, then enrich each row with founding year, funding stage and lead application. By hand: a week. Well-prompted: an afternoon. **You are not given a cleaned company list on purpose** — assembling one from a live source *is* the repeatable method the challenge asks for, and a hand-curated spreadsheet would be stale by the time you pitched it.
- **Structured extraction from unstructured documents.** Pull cohort size, endpoint, sponsor, completion date from 50 trial records into one table.
- **Cross-document synthesis.** "Across these 12 companies' filings, what did each say about pricing strategy?"
- **Adversarial review.** Use a model to attack your own scoring frame before the jury does.

### Where AI will quietly ruin your case

- **Any specific number produced from memory.** Prices, revenues, deal values, dates, cohort sizes — these hallucinate with total confidence. Every such number must come from a document you opened. *Two of the errors corrected in this brief entered exactly this way.*
- **Market-size figures.** The "$X billion by 2032" genre is the most polluted data in this industry. Source it, and say who paid for the report.
- **Entity confusion.** This industry is full of near-identical names, and models silently merge them. Real examples you will hit: *GeneCentric Diagnostics* vs *GeneCentric Therapeutics* · *miRoncol Diagnostics* vs *miRoncol Health* · *OXcan* vs *Oxford Cancer Analytics* (the same company under two names) · *EarlyDiagnostics* vs *EarlyDx* · *Exact Sciences* vs *Exact Biosciences* (different companies, both in Madison, Wisconsin) · *Standard BioTools* vs *SomaLogic* vs *Illumina* (one asset, three owners since 2024). **Resolve entities before you count anything**, and record which name you canonicalised to.
- **Unit and magnitude errors.** aM/fM/pM, pg/mL vs mol/L, per-mL vs per-sample. Models slip a factor of ten and keep the confident tone. **Always convert to molecules per sample and sanity-check.**
- **Recency.** Much moved in 2025–2026: Abbott/Exact, Illumina/SomaLogic, GRAIL's endpoint miss, the first FDA-cleared Alzheimer's blood test, Alamar's IPO, Nautilus's Voyager launch. Training data may pre-date all of it. **Search, don't recall.**

### A workable discipline

1. Use AI to *generate the search*; open the primary source yourself.
2. Keep a **source column** in every table. Empty source = hypothesis, not finding.
3. Two-source rule for any figure that carries weight in a recommendation.
4. **State what you could not verify.** A clearly-marked gap beats a confident guess — and the jury includes people who know which numbers are shaky.
5. **Show your pipeline.** The prompt chain or script that turns raw inputs into the scored map *is* a deliverable, and directly answers the "repeatable method" criterion.

---

## 16. Where to get company and market data

You are given this brief and the company deck — no pre-built dataset. That is deliberate. Every source below is free, live, and structured enough to build from, and building your own census is more defensible than inheriting someone else's spreadsheet.

### Company censuses — who exists

| Source | What it gives you | Why it is good |
|---|---|---|
| **[ADLM Annual Meeting exhibitor directory](https://meeting.myadlm.org/exhibitors)** — and the [browsable 2026 listing of ~605 companies](https://meddeviceguide.com/conferences/adlm-2026) | Essentially the entire clinical-diagnostics industry, with product categories and booth data | The single best free company census in this field. Anyone selling into clinical labs exhibits here |
| **[openFDA device APIs](https://open.fda.gov/apis/device/510k/)** — [510(k)](https://open.fda.gov/apis/device/510k/), [PMA](https://open.fda.gov/apis/device/pma/), plus [bulk downloads](https://open.fda.gov/data/downloads/) and [downloadable 510(k) files](https://www.fda.gov/medical-devices/510k-clearances/downloadable-510k-files) | Every cleared/approved device with applicant company, date, product code, decision | **The highest-signal dataset in this brief.** It tells you who actually got through, when, and via which route. Query by product code to get an entire competitive segment |
| **[FDA device databases hub](https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/medical-device-databases)** · [establishment registration & listing](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfrl/textsearch.cfm) | Registered manufacturers and their listed devices | Catches companies that never filed a 510(k) |
| **[CORDIS projects](https://cordis.europa.eu/projects)** · [CORDIS data services](https://cordis.europa.eu/about/services) | Every EU-funded project with full participant lists, budgets, dates | Finds European companies and academic groups *before* they are commercially visible — and shows who already collaborates with whom |
| **[Dealroom](https://app.dealroom.co/companies.startups)** ([free tier](https://www.dealroom.co/for-builders/)) | Startup/scaleup profiles, funding rounds, ecosystem filters | Strong European and Nordic coverage where US-centric databases are thin |
| **[European Liquid Biopsy Society — network & working groups](https://www.uke.de/english/departments-institutes/institutes/tumor-biology/european-liquid-biopsy-society-elbs/network/index.html)** | Member companies and academic groups in liquid biopsy specifically | A curated, domain-exact list — closest thing to a ready-made liquid-biopsy census |
| **[ADDF Diagnostics Accelerator portfolio](https://www.alzdiscovery.org/research-and-grants/diagnostics-accelerator/portfolio)** · [full ADDF portfolio](https://www.alzdiscovery.org/research-and-grants/portfolio) | Every company funded to build a neurodegeneration diagnostic | For the neurology thread this is the definitive competitor list, and it names who is funded to do what |
| **[Healthtech Finland members](https://teknologiateollisuus.fi/healthtech/en/association/members/)** | The Finnish health-technology industry | The local ecosystem, and the most reachable set of potential partners and first customers |

**Method note.** Cross-reference two or three of these and the picture sharpens fast: a company in the ADDF portfolio *and* holding a 510(k) is at a different stage from one appearing only in CORDIS. **Stage inference from source overlap** is a cheap, repeatable signal — and it is exactly the kind of "clear, repeatable way of looking at the data" the challenge asks for.

### Deals, filings and financials

- **[SEC EDGAR full-text search](https://efts.sec.gov/LATEST/search-index?q=)** — 10-K/10-Q filings. Test volumes, ASPs and pricing strategy live in the "Business" section and MD&A. The single best source for real numbers on US-listed comparables
- Investor relations: [Quanterix](https://ir.quanterix.com) · [Guardant](https://investors.guardanthealth.com) · [Nautilus](https://investors.nautilus.bio) · [Alamar](https://alamarbio.com) · Natera · Standard BioTools · GRAIL
- Trade press: [GenomeWeb](https://www.genomeweb.com/) · [360Dx](https://www.360dx.com/) · [Fierce Biotech](https://www.fiercebiotech.com/) · [MedTech Dive](https://www.medtechdive.com/) · [Inside Precision Medicine](https://www.insideprecisionmedicine.com/)

### Evidence, trials and cost-to-prove

- **[ClinicalTrials.gov](https://clinicaltrials.gov/)** — cohort sizes, endpoints, sponsors, timelines, status. A public **v2 REST API** serves the same data programmatically (base endpoint `https://clinicaltrials.gov/api/v2/studies`; the site's API documentation section has the current query syntax), so you can pull every trial mentioning a biomarker in one call. **This is how you cost the evidence dimension (§14.1, #4)**
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) · [Europe PMC](https://europepmc.org/) (full-text search and API) · [bioRxiv](https://www.biorxiv.org/) · [medRxiv](https://www.medrxiv.org/)

### Reimbursement — who pays and how much

- **[CMS Clinical Laboratory Fee Schedule](https://www.cms.gov/medicare/payment/fee-schedules/clinical-laboratory-fee-schedule-clfs)** — downloadable files listing what Medicare actually pays per test code. If a test is not here, it is not a business yet
- Search MolDX local coverage determinations for molecular test coverage decisions

### Patents — the defensibility dimension

- **[Lens.org](https://www.lens.org/)** — free patent and scholarly search with assignee analytics; lets you see a competitor's whole portfolio and its expiry profile
- [Google Patents](https://patents.google.com/) · [Espacenet](https://worldwide.espacenet.com/)

### Biology and target prioritisation

- **[Open Targets Platform](https://platform.opentargets.org/)** — target–disease association evidence, with [bulk downloads](https://platform.opentargets.org/downloads). Directly feeds the "unmet clinical need" score
- [Human Protein Atlas](https://www.proteinatlas.org/) — expression by tissue and pathology, plus blood-biomarker candidates
- [UniProt](https://www.uniprot.org/) — use it for **molecular weights** when converting pg/mL to molar (§4.5)
- [ProteomicsDB](https://www.proteomicsdb.org/) · [TCGA / GDC](https://portal.gdc.cancer.gov/) · [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/)

### Vendor catalogues — for the commoditisation analysis

To answer "which markers are already sold by two or more vendors," scrape the catalogues directly: [Olink](https://olink.com/products/compare) · [Quanterix](https://www.quanterix.com/) · [Alamar](https://alamarbio.com/products-and-services/) · [Meso Scale Discovery](https://www.mesoscale.com/) · [Bio-Rad Bio-Plex](https://www.bio-rad.com/) · [Thermo Fisher ProcartaPlex](https://www.thermofisher.com/fi/en/home/life-science/antibodies/immunoassays/procartaplex-assays-luminex/features.html). Panel contents and list prices are public; the overlap between them is the commoditisation map.

---

## 17. Reference directory

*Datasets for building the company and market map are in §16. This section covers the regulatory frameworks, cohorts and primary sources you will need alongside them.*

### Regulatory frameworks
- [FDA In Vitro Diagnostics guidance](https://www.fda.gov/medical-devices/in-vitro-diagnostics) — classification, 510(k) vs PMA, what each route demands
- [FDA press announcements](https://www.fda.gov/news-events/fda-newsroom/press-announcements) — first-in-class clearances land here first
- [EU IVDR 2017/746](https://health.ec.europa.eu/medical-devices-topics_en) — the European regime and its evidence requirements
- [EMA scientific advice & biomarker qualification](https://www.ema.europa.eu/en/human-regulatory-overview/research-development/scientific-advice-protocol-assistance) — the EU route to getting a novel biomarker formally qualified for trial use

### Cohorts & biobanks — the real gating resource
Sample access, not technology, is what usually decides whether a validation study can happen at all. Treat this as a strategic dimension, not a footnote.

- [UK Biobank](https://www.ukbiobank.ac.uk/) and the [Pharma Proteomics Project (UKB-PPP)](https://www.ukbiobank.ac.uk/projects/large-scale-proteomic-profiling-to-facilitate-genetics-guided-drug-discovery-and-precision-medicine-the-uk-biobank-pharma-proteomics-project-ukb-ppp/) · [UKB-PPP open data on AWS](https://registry.opendata.aws/ukbppp/) — the cohort that made Olink's reputation (§9). Read how that deal was structured
- [FinnGen](https://www.finngen.fi/en) — Finnish genomic + registry cohort at national scale. **Its proteomic depth is far smaller than its genomic scale, and the exact numbers matter for any Finnish validation plan:** [FinnGen reports](https://www.finngen.fi/en/other-biological-data) proteomics on **6,350 plasma samples (Olink 3K/5K)** plus **880 samples (SomaLogic)**, with ~5,000 further samples planned by end of 2027 — against a genomic cohort of roughly half a million. Ample for discovery and marker prioritisation; not a population-screening validation set on its own. See also the [FinnGen Handbook proteomics documentation](https://docs.finngen.fi/finngen-data-specifics/red-library-data-individual-level-data/omics-data/proteomics/finngen-3-proteomics-data)
- [Fingenious — Finnish biobank access](https://site.fingenious.fi/en/) — the practical route into Finnish samples, and the most realistic near-term option for a Helsinki company
- [BBMRI-ERIC](https://www.bbmri-eric.eu/) — pan-European biobank infrastructure
- [All of Us (NIH)](https://allofus.nih.gov/) · [PPMI — Parkinson's](https://www.ppmi-info.org/) · [ADDF Diagnostics Accelerator biobank sharing](https://www.alzdiscovery.org/research-and-grants/diagnostics-accelerator/biobank-sharing-program)

### EU funding, consortia & networks — who is paid to work on what, with whom
- [European Innovation Council](https://eic.ec.europa.eu/) · [Innovative Health Initiative project factsheets](https://www.ihi.europa.eu/projects-results/project-factsheets) · [European Liquid Biopsy Society](https://www.uke.de/english/departments-institutes/institutes/tumor-biology/european-liquid-biopsy-society-elbs/index.html) · [EPND — European Platform for Neurodegenerative Diseases](https://epnd.org/)

### Competitor primary sources
- [Nautilus Voyager launch](https://investors.nautilus.bio/news-releases/news-release-details/nautilus-biotechnology-unveils-voyager-platform-enabling-single) · [Olink product comparison](https://olink.com/products/compare) · [NULISA in *Nature Communications*](https://www.nature.com/articles/s41467-023-42834-x) · [Quanterix](https://www.quanterix.com/) · [Thermo Fisher/Olink acquisition](https://ir.thermofisher.com/investors/news-events/news/news-details/2024/Thermo-Fisher-Scientific-Completes-Acquisition-of-Olink-Announces-Commencement-of-Subsequent-Offering-Period/default.aspx)

### Finnish life-science ecosystem
[Nightingale Health](https://nightingalehealth.com/) · [Genomill](https://genomill.com/) · [Uniogen](https://uniogen.com/) · [Medix Biochemica](https://www.medixbiochemica.com/) · [HyTest](https://www.hytest.fi/home) · [Hidex](https://www.hidex.com/) · [Aidian](https://www.aidian.eu/) · [Labsystems Diagnostics](https://www.labsystemsdx.com/) — full member list via [Healthtech Finland](https://teknologiateollisuus.fi/healthtech/en/association/members/)

---

## 18. The questions Proteins.1 most wants answered

Pick a subset. **Depth beats coverage.**

**On the leaders**
1. For companies acquired or partnered at high value: **what specifically did they have to prove** to the acquirer? How many tests had they run? How much had they raised? What was the state of their evidence at the moment of the deal?
2. **Why has a genuine sensitivity lead (Quanterix) not converted into growth**, while a narrower but decision-linked product (Natera Signatera) has?
3. Which came first for the winners — regulatory clearance, guideline inclusion, or reimbursement? Is there a dominant sequence?
4. Nautilus is running the RUO→commercial playbook in public right now. **What is it doing that Proteins.1 should copy, and what should it avoid?**

**On the market**
5. Across plex levels (1, 4, 10, 50, 300, 5,000) and customer segments (academic/RUO, clinical diagnostics, pharma discovery, pharma trials), what is the **realistic price per test and per data point**, and what volumes does each segment actually absorb?
6. Which marker classes are commoditised, which are specialty-priced, and which have **no commercial equivalent**?
7. **Where does attomolar sensitivity actually buy something?** (See §4.5 — this may be the highest-value question in the brief.)
8. Has ultra-sensitivity commanded a durable price premium historically, or does it erode?

**On the route to market**
9. Of the five revenue models in §5, which should Proteins.1 pursue first, and what do the comparables say?
10. Where is the fastest credible path from working platform to paying customer — and who is that first customer, by name or by type?
11. What is the strongest defensible wedge: a disease area, a marker class, a customer segment, or a workflow advantage?
12. **What should Proteins.1 *not* do**, based on who has tried it and failed?

---

## 19. Deliverables and evaluation

> *Proposed format — confirm final requirements with Helsinki Think Company on the day.*

**Deliverables**
1. **Interactive prototype / dashboard** demonstrating the opportunity-mapping tool or workflow.
2. **Slide deck**, max 10 slides: selected opportunities, technical feasibility, competitive positioning, GTM sequence.
3. **Executive summary**, 2–3 pages: methodology, scoring design, data sources, recommendations, and an explicit list of what you could not confirm.

**Rubric**

| Category | Weight | Criteria |
|---|---|---|
| **Scientific & analytical rigour** | 25% | Correct handling of sensitivity, units and biomarker biology; proven results kept distinct from vendor claims and estimates; arithmetic that survives checking |
| **AI & methodological innovation** | 25% | Real use of AI in collection, structuring and interpretation; transparent, repeatable scoring; public data integrated |
| **Market strategy & commercial viability** | 25% | Realistic RUO → LDT → IVD sequence; competitor positioning; named customer targets; regulatory and reimbursement understanding |
| **Clarity & pitch quality** | 25% | Clear communication, an argued point of view, actionable for a real decision |

**What earns marks beyond the rubric:** finding an error in this brief; killing one of our own hypotheses with evidence; naming a customer or partner we have not considered; telling us something we did not want to hear and proving it.

---

## 20. Ground rules

- **Confidentiality.** This brief and the company deck are provided for the sprint. Do not republish them. Company-internal figures — funding, cost structure, target lists, and the GTM assumptions in §12 — should not appear in any public output without checking with Prateek first.
- **Accuracy over polish.** A confident wrong number costs more than an acknowledged gap.
- **Cite everything.** Source column, footnotes, or a linked appendix — any format, but present.
- **Separate what is proven from what is claimed.** Say which of your figures are measured results, which are a company's claim about itself, and which are your own estimate. This is scored.
- **Outside views welcome.** If your analysis says the current strategy is wrong, say so and show why. That is the most useful possible outcome for us.
- **Ask.** The people behind the technology — microfluidics, photonics, regulated medical devices — are on hand during the sprint. A five-minute question can save three hours.

---

## 21. Glossary

| Term | Meaning |
|---|---|
| aM / fM / pM / nM | atto- (10⁻¹⁸) / femto- (10⁻¹⁵) / pico- (10⁻¹²) / nanomolar (10⁻⁹) |
| AMT | **Affinity Mediated Transport** — Proteins.1's enzyme-free amplification method |
| Aβ42/40 | Amyloid-beta 42:40 ratio; Alzheimer's blood biomarker |
| CDx | Companion diagnostic — test paired with a specific drug |
| cfDNA / ctDNA | Cell-free DNA / circulating tumour DNA |
| CLFS | US Medicare Clinical Laboratory Fee Schedule |
| CLIA / CAP / ISO 15189 | Clinical laboratory accreditation regimes |
| CRO | Contract Research Organisation |
| ELISA | Enzyme-Linked Immunosorbent Assay — the classic protein test |
| EV | Extracellular vesicle |
| GFAP | Glial fibrillary acidic protein; astrocytic activation marker |
| IVDR | EU In Vitro Diagnostic Regulation 2017/746 |
| LDT | Laboratory Developed Test |
| LOD / LLOQ | Limit of Detection / Lower Limit of Quantification |
| MCED | Multi-Cancer Early Detection |
| MolDX | Medicare programme governing molecular diagnostic coverage |
| MRD | Minimal/Molecular Residual Disease |
| NfL | Neurofilament light chain; axonal damage marker |
| NPX | Olink's relative protein expression unit |
| NULISA | Alamar's nucleic-acid-linked immunoassay |
| ORF1p | LINE-1 Open Reading Frame 1 protein; multi-cancer biomarker |
| PEA | Proximity Extension Assay — Olink's technology |
| Plex | Number of analytes measured simultaneously |
| Proteoform | A distinct molecular form of a protein (splice, PTM, cleavage variant) |
| p-tau217 | Phosphorylated tau 217; leading Alzheimer's blood biomarker |
| RUO | Research Use Only |
| SAA | Seed Amplification Assay (α-synuclein) |
| Simoa | Single Molecule Array — Quanterix's digital ELISA platform |
| TAM / SAM | Total / Serviceable Addressable Market |

---

*Questions before or during the sprint: prateek@proteins1.com*
