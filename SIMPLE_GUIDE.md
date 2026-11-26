# SMIT — The Simple Guide

Start here. The other guides have more detail, but this page is all you need to run the project.

## 1. What is the project about?

We want to know: **does doing another task while remembering something make your memory worse — and does it matter what kind of task it is?**

We test this with a short computer game:

1. A grid of 9 squares appears with **4 blue squares**. You remember where they are.
2. For 3 seconds you either:
   - **do nothing** (Control),
   - **check a sum** like `7 + 6 = 13` (Numbers), or
   - **look at an orange grid** and say if it is symmetrical (Visual).
3. A second blue grid appears. Press **F if it is the same**, **J if one square moved**.

We measure how often people are **correct** and how **fast** they answer, in each of the three versions.

**Our prediction:** doing a sum or looking at another grid makes memory worse, and the orange grid hurts the most (because it uses the same "picture memory").

## 2. What has already been built (by me)

| Part | What it is |
|---|---|
| The game | Runs in a web browser. Saves every answer automatically. |
| Researcher dashboard | A website for you to watch progress and press buttons. |
| Excel template | Use only if you collect data on paper or outside the app. |
| Automatic analysis | One button does all the statistics and graphs. |
| Automatic report | One button makes the report (PDF / Word) and the slides. |
| Research write-up | Background, hypotheses, method, references (in the `research` folder). |

All of this is finished and tested. **What's missing is real people's data** — only you can collect that.

## 3. How to start the app

Open the **Terminal** app on your Mac and type:

```bash
cd ~/Desktop/SMIT-Cognitive-Research && ./scripts/start.sh
```

Leave that window open. Then, in Chrome, go to **http://127.0.0.1:8000**

- **Take part** → the game (for participants)
- **Researcher dashboard** → for you (the password you set in `.env`)

To stop the app, press `Ctrl + C` in the Terminal window.

### Letting other computers open it (same Wi-Fi)

`start.sh` only works on **your** computer. To let other laptops on the **same Wi-Fi / network** open the test, use this instead:

```bash
cd ~/Desktop/SMIT-Cognitive-Research && ./scripts/start_network.sh
```

It prints the link to share, for example `http://10.7.20.10:8000/participate`. (The number is your computer's network address and can change when you change Wi-Fi — always use the link it prints.)

- Your computer must stay **on, awake and running** that window while people take the test. All data is still saved only on your computer.
- You must have set your own password in `.env` first (it refuses to start with `change-me-now`).
- If macOS asks "Allow incoming network connections?", click **Allow**.
- It does **not** work if the other person is on a **different network** (e.g. their home Wi-Fi or mobile data), and some college/guest Wi-Fi networks block computers from talking to each other.
- **Research note:** the design assumes everyone uses the **same computer and keyboard**. If participants use their own laptops, timing and screen size will differ — mention this as a limitation in the report.

## 4. The procedure — step by step

### Step 1 — Fill in your details (5 minutes)
Dashboard → **Settings**. Type your university, your names, professor's name and contact email. Click **Save**.

### Step 2 — Try it yourself (10 minutes)
Dashboard → **Pilot mode** → **Start pilot session**. Play the whole game once so you know what participants will see. (Pilot data is kept separate and never counted.)

### Step 3 — Pilot test with 3–5 friends (1 hour)
Same as Step 2, but with friends who will **not** be in the real study. Ask them afterwards: Was anything confusing? Was it too easy or too hard? Write their answers in **Settings → Pilot observations**.

### Step 4 — Lock the settings (1 minute)
Dashboard → **Configuration** → click **Lock** on version 1 and write one sentence why (e.g. "Pilot with 4 people went fine"). Now the real study is open.

### Step 5 — Test at least 20 people (≈ 20 minutes each)
For each person:
1. Same laptop, quiet room, plug in a normal (wired) keyboard if you have one.
2. Open **http://127.0.0.1:8000/participate** and let them read and agree.
3. They fill in age, gender, course, email — then play.
4. At the end it says "Thank you" and "data saved". Done.

Check **Dashboard → Overview** to see how many people are finished (target: 20).

### Step 6 — Get the results (2 minutes)
Dashboard → **Analysis** → **Run Analysis**. You'll see the numbers, which predictions were supported, and the graphs.

### Step 7 — Get the report and slides (2 minutes)
Dashboard → **Reports** → **Generate Research Report**, then **Regenerate presentation**. Download the files.

### Step 8 — Read and fix the report
The computer writes a first draft of the Discussion. **Read it, change the wording into your own, and check it makes sense.** Then submit.

## 5. What you hand in

1. **The task** → this project folder (or the GitHub link).
2. **The data** → Dashboard → Import/Export → download **.xlsx** (no emails are included).
3. **The report** → the PDF/Word from Step 7, after you've edited it.
4. **The slides** → from Step 7.

## 6. If you collected data on paper instead

Download `templates/SMIT_Data_Collection_Template.xlsx`, fill it in, then drag it into **Dashboard → Import / Export**. The app checks it, tells you about any mistakes, and you click **Confirm import**. Then do Steps 6–8.

## 7. Help

| Problem | Fix |
|---|---|
| "The study is not open yet" | Do Step 4 (Lock). |
| Page won't load | The Terminal from Section 3 isn't running — start it again. |
| Forgot password | It's `change-me-now` (you can change it in a file called `.env`). |
| A participant wants to quit | They press **Esc**, then **Stop and withdraw**. |
