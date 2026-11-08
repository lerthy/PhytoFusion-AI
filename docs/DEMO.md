# Demo recording script (2 to 3 minutes)

A click-by-click run of the live app that fits the pitch. Every step uses a one-click example, so nothing needs
typing and nothing writes to the database by accident. Live site: <https://photofusionai.netlify.app>

## Before you press record

1. **Wake the backend.** Open `https://<your-render-service>.onrender.com/health` and wait for `ok`
   (the free plan sleeps; the first request can take a minute).
2. **Warm the data.** Open Genomes once and let both plants load, then run one gene search (Compare → *Don’t know the gene ID?*) and one comparison. The first gene search loads the donor’s proteins and can take about 20 seconds; later ones take a few. This avoids a visible wait.
3. **Fill the two empty tables** so Home does not show zeros:
   Evidence → *Fill in the key paper* → *Add*, and Pathways → *Try the KPS example* → *Save this pathway*
   (name it "KPS enzymes"). These two writes are yours to make; the app never does them on its own.
4. **AI explanations (optional).** The *Explain in plain words* button needs `AI_API_KEY` set in Render.
   Without it the button says AI is not switched on. Skip that step in the video if it is not set.
5. Use a 1440 by 900 browser window in light mode, hide bookmarks, close other tabs.
   On a Mac: Shift-Command-5, "Record Selected Portion", microphone on.

## The run

| Time | Screen | Do | Say (from the pitch script) |
|---|---|---|---|
| 0:00 | About | Let the hero build; point at the glowing orange stretch. Scroll slowly through the three-step story. | "Explore, on paper, what moving a gene between two medicinal plants could mean. Nothing is edited or built." |
| 0:25 | Home | Click **Open the app**. Point at the steps and the *Your data* panel. | "Three steps, and one clear next step." |
| 0:35 | Genomes | Both plants are already loaded. Click the **Sbar9A9T61** button under the donor map. | "Real published genomes: 30,313 and 34,909 genes. Here is the KPS gene on its chromosome." |
| 1:00 | Compare | Open **Don’t know the gene ID?**, click **Try the paper’s SbarKPS2 protein**, then **Find genes**. Point at `Sbar9A9T61` marked *Same protein* (100%), click **Use this gene**, add `Sbar9A10T43`, then host *S. baicalensis*, donor *S. barbata* → **Compare**. Point at the bars and "mutual best match". Click **Explain in plain words**. | "The paper names the enzyme but not our gene ID. So we search its published protein sequence against the genome with BLAST: the top hit is the same protein, at 100%. Now: which host gene is closest? A reciprocal check confirms it. The AI only restates these facts and says so." |
| 1:30 | Pathways | Click **Try the KPS example**; click one gene node. | "Every step carries a source and an evidence level." |
| 1:50 | Evidence | Show the key paper recorded as *moderate*. | "Evidence is a class, never a score." |
| 2:00 | Scenario → Report | Click **Use the case study**, then **Show me what this could mean**. Scroll the report: diagram, *What we don't know*, *Limits*. | "Hypothetical. The insertion site is not chosen. What we don't know is listed, and the limits are stated." |
| 2:40 | Report | Stay on the limits box. | "No engineered plant exists, and this says nothing about how well a medicine would work." |

Keep it under three minutes. If a step is slow on camera, cut it in editing; do not fake results.

## If something goes wrong

- **Compare is slow or fails:** the backend is waking up. Wait for `/health` and try again.
- **Explain button says "not switched on":** the AI key is not set in Render. Skip it.
- **Home shows zeros:** do step 3 above.
- **Anything else:** `docs/CICD.md` and `docs/DEPLOY.md` list the checks and settings.
