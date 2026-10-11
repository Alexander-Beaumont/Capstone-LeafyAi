# leafyAI User Manual

**Product:** leafyAI  
**Version:** 0.0.0  
**Date:** 11 October 2026  

This manual explains how to use leafyAI. It is written for the person who runs the hydroponic farm, not for the person who builds the software.

The product is leafyAI. The logo on the page reads **LeafyAI**, and the browser tab reads **LeafyAi**.

[Screenshot: Browser tab and LeafyAI logo]

---

## Table of contents

1. [Introduction](#introduction)
2. [Before you begin](#before-you-begin)
   - [What you need](#what-you-need)
   - [Accounts](#accounts)
   - [What the app can control](#what-the-app-can-control)
3. [Getting started](#getting-started)
   - [Start leafyAI](#start-leafyai)
   - [Create an account](#create-an-account)
   - [Log in](#log-in)
   - [Your first five minutes](#your-first-five-minutes)
4. [Interface overview](#interface-overview)
   - [Wide screen](#wide-screen)
   - [Narrow screen](#narrow-screen)
   - [Pages](#pages)
5. [Feature guides](#feature-guides)
   - [Watch the farm](#watch-the-farm)
   - [Turn devices on or off](#turn-devices-on-or-off)
   - [Read recommendations on the farm page](#read-recommendations-on-the-farm-page)
   - [Run the AI Agent](#run-the-ai-agent)
   - [Record growing areas](#record-growing-areas)
   - [Record a plant batch](#record-a-plant-batch)
   - [Move a batch](#move-a-batch)
   - [Harvest or end a batch](#harvest-or-end-a-batch)
   - [Review sensor history](#review-sensor-history)
   - [Review individual readings](#review-individual-readings)
   - [Review camera pictures](#review-camera-pictures)
   - [Review past AI runs](#review-past-ai-runs)
6. [Settings and personalisation](#settings-and-personalisation)
   - [What you can change](#what-you-can-change)
   - [Create a farm](#create-a-farm)
   - [Delete a farm](#delete-a-farm)
   - [AI configuration](#ai-configuration)
   - [Sensor ingestion](#sensor-ingestion)
   - [Cameras](#cameras)
7. [Managing your account and data](#managing-your-account-and-data)
   - [What is stored](#what-is-stored)
   - [Log out](#log-out)
   - [Password and profile](#password-and-profile)
   - [Delete data](#delete-data)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)
10. [Glossary](#glossary)
11. [Getting help](#getting-help)

---

## Introduction

leafyAI is a website for a hydroponic farm. You run it on your own computer with Docker, then open it in a browser. You use it to:

- See live readings from the farm sensors.
- Turn farm outlets on and off, including an emergency stop.
- Keep a record of growing areas, plant batches, moves, harvests, and ended crops.
- Take pictures from the farm cameras and look back through them.
- Ask the built-in assistant for recommendations, and let it turn the fan and grow lights on or off when a safety check passes.

The people who use leafyAI are farm operators. You need everyday computer skills. You do not need to write code.

A new farm starts with a controller, the standard sensors, and two levels (level 1 and level 2). You add the sensor addresses, cameras, trays, and plant batches yourself.

**Warning:** Every person who can log in can see every farm, change settings, switch outlets, and delete a farm. Treat the username and password like a key to the grow room.

---

## Before you begin

### What you need

| Need | Detail |
| --- | --- |
| Device | The computer that will run leafyAI, with the leafyAI project folder and a current web browser. Use leafyAI in a browser on that same computer. The layout changes when the window is narrower than 1000 pixels. |
| Docker | [Docker Desktop](https://www.docker.com/products/docker-desktop/) on that computer. |
| Connection | On the computer that runs leafyAI, open `http://localhost:5173`. Sensor boxes and cameras are contacted by that computer, so your phone does not talk to them directly. |
| Browser permissions | leafyAI does not ask for your camera, microphone, location, or notification permission. Pictures come from the farm cameras on the network. |
| Extra accounts | A leafyAI username and password. A paid or local AI service is optional. The built-in **mock** choice works without an extra account. |

The product is leafyAI. The logo on the page reads **LeafyAI**, and the browser tab reads **LeafyAi**.

[Screenshot: Sign-in page on a wide monitor]

### Accounts

You create one username and one password inside the app. leafyAI does not ask for an email address, and it does not send a confirmation message.

There are no separate roles. A signed-in person can use every page.

You stay signed in on that browser until you click **Log Out**, or until the saved sign-in can no longer be renewed. That renewal window is about 30 days. When it ends, the app returns you to the sign-in page.

### What the app can control

On **Farm Overview**, under **Device Control**, these outlets have switches:

| Switch label | What it is |
| --- | --- |
| **pH Doser** | Outlet for the pH dosing device |
| **EC Doser** | Outlet for the nutrient (electrical conductivity) dosing device |
| **Irrigation Pump** | Outlet for the irrigation pump |
| **Farm Fan** | Outlet for the farm fan |
| **Light Level 1** | Outlet for the lights on level 1 |
| **Light Level 2** | Outlet for the lights on level 2 |

You can switch any of these by hand.

The AI assistant may switch **Farm Fan**, **Light Level 1**, and **Light Level 2** by itself after a safety check passes. Advice about the pump, the dosers, water, and harvest stays on the screen for you to read. The assistant does not switch those outlets.

---

## Getting started

You start leafyAI on your own computer with Docker, then open it in a browser. Docker is the program that starts the website.

### Start leafyAI

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) if it is not already installed.
2. Open Docker Desktop and wait until it is running.
3. Open a terminal in the leafyAI project folder.
4. If this computer has never run leafyAI, copy the example settings file.

   On a Mac or Linux computer:

   ```bash
   cp .env.example .env
   ```

   On Windows PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Open the `.env` file and fill in the passwords and keys. Ask the person who manages the lab if you need help. Keep that file private.
6. Start leafyAI:

   ```bash
   docker compose up --build
   ```

7. Wait until the start finishes.
8. Leave that terminal open. Closing it stops the website.
9. Open `http://localhost:5173` in a web browser.

The first screen is **Sign Up**.

**Note:** Open leafyAI on the same computer that is running Docker. The address is `http://localhost:5173`. You need the leafyAI project folder on that computer before step 3. Ask the person who gave you leafyAI if you do not have that folder yet.

### Create an account

The app opens on **Sign Up**.

[Screenshot: Sign Up form]

1. Click the **Username** box and type a name. Use letters and numbers. The box allows up to 30 characters. A counter under the label shows how many characters you have used, for example `8/30`.
2. Click the **Password** box and type a password. The box allows up to 15 characters.
3. Click the eye icon at the right of a password box if you want to see what you typed.
4. Click **Confirm Password** and type the same password again.
5. Click **Sign Up**.

While the app is working, the button label is replaced by a spinning icon.

**Expected result:** You land on **Farm Overview**. If you have no farms yet, the page says **No farms yet.** and links to **Create a farm in Settings.**

**Password rules the form checks**

| Rule | Message in the **Note** box |
| --- | --- |
| Username is empty | **Enter an username** |
| Password is shorter than 6 characters | **Password too short** |
| Password has no capital letter | **Password needs atleast one capital letter** |
| Password has no number | **Password needs atleast one number** |
| Password has no symbol (a character that is not a letter or number) | **Password needs atleast one special character** |
| **Confirm Password** is different | **Passwords do not match** |

On **Sign Up**, the **Note** box joins the username message and the password message with a comma. Click **Close** to dismiss it.

**Warning:** A password that passes the form can still be rejected. Use 8 to 15 characters. Avoid a common password, and avoid a password that is too similar to the username. If the server rejects the account, the **Note** box says **Invalid username or password**. That same sentence appears when the username is already taken.

If leafyAI cannot be reached, the **Note** box says **Could not connect to backend**. Start it with Docker. See [Start leafyAI](#start-leafyai).

### Log in

1. On the **Sign Up** card, click **Log In** under **Already have an account?**
2. Type your **Username**.
3. Type your **Password**.
4. Click **Log In**.

[Screenshot: Log In form]

**Expected result:** You land on **Farm Overview**.

The **Log In** form checks the password with the same rules as sign up. It does not check that the username box is filled in before it sends the form. A wrong name or password shows a **Note** titled box with **Invalid username or password**. Click **Close**.

To return to sign up, click **Sign Up** under **Don't have an account?**

If you are already signed in and you open the sign-in address, the app sends you to **Farm Overview**.

### Your first five minutes

1. Create an account, or log in.
2. Read the **Farm Overview** page. With no farm selected, follow the link **Create a farm in Settings.** or click **Settings**.
3. On **Settings**, leave **New farm** selected.
4. Type a name in **Name**. **North rack** is the hint text in the box.
5. Type a place in **Location** if you want one. **Lab** is the hint text. You can leave **Location** empty.
6. Click **Create farm**.
7. Read the **Farm created** message. It tells you the farm has a controller, standard sensors, and levels 1 and 2.
8. Click **Close**.
9. Open the farm list in the bar. It starts as **Select farm**. Click your new farm’s name.
10. Click **Sensor ingestion** and enter the two sensor web addresses if you have them. Turn **Enabled** on, then click **Save**. See [Sensor ingestion](#sensor-ingestion).
11. Click **Farm Overview** and confirm the farm name is selected. Sensor cards show **—** until a reading arrives.

[Screenshot: Farm created message]

---

## Interface overview

### Wide screen

After you log in, a window that is at least 1000 pixels wide shows a fixed bar on the left.

[Screenshot: Left navigation on Farm Overview]

From top to bottom:

| Item | What it does |
| --- | --- |
| **LeafyAI** | The logo. **AI** is highlighted. |
| Farm list | Shows **Select farm** until you pick one, then shows the farm name. |
| **Farm Overview** | Live readings, advice, and outlet switches. |
| **AI Agent** | Recommendation runs and a button to generate a new one. |
| **Growth & Harvesting** | Growing areas and plant batches. |
| **History** | Past readings, pictures, and AI runs. |
| **Settings** | Create a farm, AI setup, sensors, and cameras. |
| **Log Out** | Signs you out and returns you to the sign-in page. |

The current page is highlighted. The main content sits to the right of this bar.

Before you log in, the left bar is hidden. A thin top bar shows **LeafyAI** and a **Sign Up** button, even on a wide monitor.

### Narrow screen

When the window is narrower than 1000 pixels, the left bar is replaced by a top bar.

[Screenshot: Narrow top bar and menu]

| Item | What it does |
| --- | --- |
| **LeafyAI** | The logo, on the left. |
| Farm list | In the middle, after you are signed in. |
| **Sign Up** | Shown before you are signed in. It opens the sign-in page. |
| Menu icon | Three stacked lines, on the right, after you are signed in. |

1. Click the menu icon.
2. Click **Farm Overview**, **AI Agent**, **Growth & Harvesting**, **History**, **Settings**, or **Log Out**.

### Pages

| Page | How you know you are there | Main job |
| --- | --- | --- |
| **Sign Up** / **Log In** | Card in the centre | Create an account or sign in |
| **Farm Overview** | Title **Farm Overview** | Readings, waiting advice, outlet switches, status cards |
| **AI Agent** | Title **AI Agent** | Latest recommendations and **Generate now** |
| **Growth & Harvesting** | Title **Growth & Harvesting** | Areas, active batches, archived batches |
| **History** | Title **History** | **Sensor history**, **Readings**, **Cameras**, **AI decisions** |
| **Settings** | Title **Settings** | **New farm**, **AI configuration**, **Sensor ingestion**, **Cameras** |

If no farm is selected, **Farm Overview**, **Growth & Harvesting**, and **History** show one of these lines:

- **No farms yet. Create a farm in Settings.**
- **Select a farm in the navigation bar.**

**Settings** shows **No farms yet. Create one with the form below.** when you have zero farms.

A red line at the top of a page is an error from loading the farm. Read it and use [Troubleshooting](#troubleshooting).

Dates on cards are written as day/month/year. A time may be added, for example `11/10/2026 9:5`. The date picker uses a padded clock, for example `11/10/2026 09:05`.

---

## Feature guides

### Watch the farm

Use **Farm Overview** whenever you want the current state of the selected farm.

[Screenshot: Farm Overview]

1. Click **Farm Overview**.
2. Choose the farm in the farm list if the page says **Select a farm in the navigation bar.**
3. Read the five reading cards across the top.
4. Read **Awaiting Decisions**.
5. Use **Device Control** if you need to switch an outlet. See [Turn devices on or off](#turn-devices-on-or-off).
6. Read the smaller status cards along the bottom.
7. Click a card to open the matching part of **History**.

The page refreshes on its own. The text at the top right counts down, for example **Next refresh in 12s**. While it is loading, that text says **Refreshing…**. Click the round-arrow icon to refresh immediately. The icon is labelled **Refresh** for screen readers.

**Reading cards**

| Card | Meaning | Grey card means |
| --- | --- | --- |
| **Temperature** | Air temperature in °C | The reading is missing or not fresh |
| **Humidity** | Relative humidity in % | The reading is missing or not fresh |
| **pH** | How acidic or alkaline the water is | The reading is missing or not fresh |
| **EC** | Electrical conductivity, a measure of nutrients in the water | The reading is missing or not fresh |
| **Water Level** | Reservoir water level in cm | The reading is missing or not fresh |

A card with no number shows **—**. Under the number you may see:

- A short age, such as `45s ago`, `3m ago`, or `2h ago`
- **missing**
- **stale** plus an age, such as `stale 5m ago`
- **suspect**, or a short note, when the reading is marked suspect

Water temperature and dew point are stored as well. They do not have their own cards on this page. Open **History** and choose those names there.

**Status cards**

| Card | Value you may see | Extra line |
| --- | --- | --- |
| **Ingestion** | **Healthy**, **Error**, **Off**, **None**, or **…** | **Last collection** plus a time, or **None** |
| **Fresh sensors** | A fraction such as `5/7` | A line such as `2 stale, 1 missing`, and a line such as `0 suspect quality` |
| **Cameras** | How many cameras are set up | **Next capture** plus a time, or **None** |
| **Image quality** | **PASS**, **WARN**, **FAIL**, **UNKNOWN**, or **None** | The quality sentence, or **VLM ready**, **Not VLM ready**, or **No image** |
| **AI schedule** | **On** or **Off** | **Next window** plus a time, or **None** |

**Ingestion** means “are sensor readings being collected?”. **Healthy** means the last collection worked. **Off** means collection is switched off. **None** means it is not set up. **Error** means the last collection failed.

**Tip:** Click **Temperature**, **Humidity**, **pH**, **EC**, or **Water Level** to open **Sensor history** with that sensor already chosen. Click **Ingestion** or **Fresh sensors** for sensor history. Click **Cameras** or **Image quality** for the camera gallery. Click **AI schedule** for past AI runs.

**Expected result:** You can see whether readings are fresh, whether pictures are good enough for the vision assistant, whether the AI timetable is on, and whether outlets respond.

### Turn devices on or off

Use **Device Control** on **Farm Overview** when you want to power an outlet yourself.

[Screenshot: Device Control with E-Stop]

1. Open **Farm Overview** and select a farm.
2. Find **Device Control**.
3. Click the switch beside the device name.

The switch sits to the right. A switch slid to the right and highlighted means that outlet is on. A switch slid to the left means it is off.

**Expected result:** The outlet changes, and the page reloads the device states. There is no extra “are you sure?” step for a single switch.

**Warning:** One click changes the real outlet. Check the name before you click.

If the app is still loading devices, the heading area says **Loading…**. If every outlet is unreachable, it says **Powerboard offline**. A faded switch can show a tooltip that says **Device offline**. Leave a faded switch alone. It will not change.

**Emergency stop**

1. Click **E-Stop**.
2. Read the box titled **Emergency stop?**
3. Read the line **This turns off every controlled outlet.**
4. Click **E-Stop** to go ahead, or **Cancel** to leave everything as it is.

While it is working, the button says **Stopping…**.

**Expected result:** leafyAI asks every controlled outlet to turn off: **pH Doser**, **EC Doser**, **Irrigation Pump**, **Farm Fan**, **Light Level 1**, and **Light Level 2**. Any failure is written in red under the heading.

**Tip:** Use **E-Stop** when you need every outlet off quickly. Switch individual devices back on afterwards.

### Read recommendations on the farm page

**Awaiting Decisions** on **Farm Overview** lists advice from the latest AI run that is ready for you to read. Each card is a notice. You carry out pump, doser, water, and harvest advice yourself.

[Screenshot: Awaiting Decisions]

1. Open **Farm Overview**.
2. Read the panel titled **Awaiting Decisions**.
3. If a run exists, the top right says **Last run:** followed by **VLM**, **LLM**, **LLM fallback**, or **None**, then a link **AI Agent**.
4. Read each card. The title is the type of advice. A pill says **Low**, **Medium**, or **High**. The time is on the right. The advice text is under the title. A line starting with **Reason:** explains it.

| What you see | Meaning |
| --- | --- |
| **Loading…** | The latest run is still loading |
| **No decisions waiting** | The latest run has no advice item that passed its safety check as a notice |
| **Low** | Confidence is missing or below 0.4 |
| **Medium** | Confidence is from 0.4 up to, but not including, 0.7 |
| **High** | Confidence is 0.7 or higher |

Fan and light actions that the assistant carries out itself are not listed in this panel. Open **AI Agent** or **History** to see those.

**Expected result:** You know what the assistant wants a person to consider, and how confident it was.

### Run the AI Agent

Use **AI Agent** to generate a recommendation or to read the latest ones.

[Screenshot: AI Agent page]

1. Select a farm.
2. Click **AI Agent**.
3. Read the farm name, the **Schedule on** or **Schedule off** pill, and the summary cards.
4. Read **Latest run**.
5. Open a row under **Recent runs** if you want another recent result.
6. Read **Automation policy** at the bottom.

The top right shows the farm name, or **Refreshing…** while loading. Click the round-arrow icon to refresh. The gear icon opens **Settings**.

**Summary cards**

| Card | What it shows |
| --- | --- |
| **Providers** | The language-model choice and the vision-model choice, such as `mock / mock`, plus the language-model name |
| **Next schedule** | **Off**, a date and time, **Outside window**, or **…** while loading. The time zone is the smaller line, **Australia/Melbourne** on a new farm |
| **Last input** | **VLM**, **LLM**, **LLM fallback**, or **None**. If the run fell back, the smaller line says **Fell back to sensors** |
| **Actions** | How many hardware actions were recorded, plus a summary such as `0 executed, 0 no-op, 0 failed, 1 advisory, 0 blocked` |

**Generate a run**

1. Click **Generate now**.
2. Read **Generate recommendations?**
3. Read **This starts a new recommendation run for the selected farm.**
4. Click **Generate**, or **Cancel**.

A **Generating** pill appears while the run is in progress. The button shows a spinning icon.

**Expected result:** **Latest run** fills in. A red line above the cards is the error text if generation fails.

**What a run shows**

Pills on the run can include the status (**Pending**, **Running**, **Completed**, **Failed**, **Skipped**), the input type (**VLM**, **LLM**, or **LLM fallback**), the trigger (**Manual**, **Scheduled**, or **Legacy**), and the provider and model name.

| Box | When it appears | Text you may see |
| --- | --- | --- |
| **Sensor-only fallback** | The run used sensor numbers without a picture | The stored reason, or **The run used the LLM without vision input.** |
| **Run failed** | The run failed | The stored error, or **The model returned unusable output.** |
| **Skipped** | The run was skipped | The stored reason, or **No new eligible evidence was available.** A scheduled skip often says **No new eligible sensor readings or camera images were available.** |

Under that, a full run (not the short recent-run view) lists:

- How many sensors were included, and how many were fresh, stale, missing, or suspect.
- How many images were included out of how many were eligible.
- Each sensor value, marked **reused** or **new**.
- Camera frames. Click a picture to download it. Each frame is marked **Selected** or **Rejected**, with a quality pill such as **PASS**.
- **VLM observations**, when the vision model wrote notes.
- Each recommendation, or the line **No recommendations in this run.**
- The line **No camera evidence for this run.** when no picture was attached.

Each recommendation shows:

- A name, a confidence pill (**Low**, **Medium**, or **High**), and one or more of **Automatic**, **Advisory**, **Safety blocked**, **No action**, **No-op**, **Executed**, **Hardware failed**, and **Partial**.
- The recommendation sentence.
- A **Reason:** line.
- A safety line such as **Safety passed:** or **Safety failed:** followed by an explanation. If no explanation was stored, you see **No explanation.**
- A hardware line with the target, the requested state, outlet numbers in brackets, and a result of **success**, **failed**, or **partial**.

A passed safety check with no problems uses this explanation: **Recommendation is supported by fresh relevant evidence and policy checks.**

If a light change only partly works, the details list lines such as **Outlet Light Level 1 succeeded (ON).** and **Outlet 6 failed:** plus the error.

**Recent runs** shows up to three runs. Each row is labelled **Run** plus a number, the time, and **Details** or **Hide**. Click the row to switch. The short view shows the pills only. **Details** shows the full write-up. If the list is empty, the page says **No recent runs.** If there has never been a run, **Latest run** says **No recommendation run exists for this farm yet.**

**Automation policy** says:

> Fan and grouped grow lights can execute automatically after a passed safety check. Pump, doser, water, and harvest recommendations stay advisory.

It also says the current mappings are fan 4, and grouped lights 5 and 6, and **There is no actuator-mapping API.** Those outlet numbers are fixed on this screen. The link **Open farm overview** returns you to **Farm Overview**.

**Tip:** Set the provider and the timetable under **Settings** before you rely on **Schedule on**. See [AI configuration](#ai-configuration).

**Common mistakes**

- Generating before a farm is selected. Choose a farm first.
- Expecting the pump or a doser to switch itself. Those stay as advice.
- Treating **Awaiting Decisions** as a queue you must approve. It is a reading list.

### Record growing areas

A growing area is a named tray or zone on level 1 or level 2, with a number of slots. Create one before you create a plant batch.

[Screenshot: Growth and Harvesting]

1. Select a farm.
2. Click **Growth & Harvesting**.
3. In the **Growing Areas** panel, click **Edit**.
4. Leave **Edit existing growing area:** on **No**. The title reads **Create New Growing Area**.
5. Fill in the boxes. See the table below.
6. Click **Create New GA**.
7. Click **Close** if you want to leave without saving. After a successful create, the window closes by itself.

| Field | Required | Limit | Notes |
| --- | --- | --- | --- |
| **Name** | Yes | 20 characters | The name shown on the card |
| **Farm Level** | Yes | 1 digit | Must be **1** or **2**. Anything else shows **Farm level can either be 1 or 2** |
| **Slot Count** | Yes | 3 digits | A whole number of 1 or more |

Empty **Name** or **Slot Count** shows **All fields must have a value**.

**Expected result:** A new row appears under **Growing Areas**. It shows **Growing Area:** and the name, **Level:** and the number, and **Slot Count:** and the number. A coloured dot on the left is red when the area has no current batch.

Empty dashed boxes under the list are spacers so the panel stays a fixed height. They are not growing areas. The list scrolls when you have many areas.

1. Click the arrow on the right of a row to open it.
2. Read **Current Batch** and **Previous batches**.

If the area is empty, you see **No batches currently in this growing area...** and **No previous batches has used this growing area...**

Opening one row closes the row that was open before.

**Change an area**

1. Click **Edit** on **Growing Areas**.
2. Click **Yes** next to **Edit existing growing area:**. The title changes to **Edit Growing Areas**.
3. Open **Select Growing Area:** and click the name. The list starts as **Select**.
4. Type the new **Name**, **Farm Level**, and **Slot Count**. The boxes are not filled in for you. The grey hint text shows the current values.
5. Click **Update**.

**Expected result:** The window closes and the card shows the new values.

**Delete an area**

1. Open **Edit** and click **Yes**.
2. Select the area.
3. Click **Delete**.

There is no second confirmation. If a batch is still in that area, the form shows:

**Can't delete this growing area as there is a active batch occupying it. Move or terminate this batch before deleting the growing area**

Move or end that batch first, then delete the area.

Other messages:

| Message | What to do |
| --- | --- |
| **Select a growing area first** | Choose an area before **Update** |
| **Select a growing area to delete first** | Choose an area before **Delete** |
| **No growing areas exist, create one first...** | Click **No** and create one |
| **Select a farm in the navigation bar.** | Pick a farm, then try again |

**Summary cards at the top of the page**

| Card | What the number means |
| --- | --- |
| **Active Batches** | Batches whose status is **Growing** (or the word active) |
| **Completed Batches** | Batches whose status text is exactly completed. Harvested and ended batches use other words, so this card stays at **0** in normal use. Use **Archived Batches** for those |
| **Avg Batch Age** | Average age, in whole days, of batches with status **Growing**. The card can show **NaNd** when none are growing |
| **Growing Area Usage** | The percentage of growing areas that currently hold a batch. The card can show **NaN%** when you have no growing areas |

### Record a plant batch

A batch is one planting: a plant type, a stage, and the growing area it sits in. The plant date is the day you click **Create Batch**.

[Screenshot: Create Batch window]

1. Create a growing area that does not already hold a current batch.
2. On **Growth & Harvesting**, in **Active Batches**, click **Edit**.
3. Leave **Edit existing batch:** on **No**. The title reads **Create Batch**.
4. Fill in every field in the table.
5. Click **Create Batch**.

| Field | Required | Choices or limit |
| --- | --- | --- |
| **Plant Type** | Yes | Up to 20 characters |
| **Select Growth Stage:** | Yes | **seedling**, **early**, **growth**, **mature** |
| **Status:** | Yes | **active**, **harvested**, **failed** |
| **Select Growing Area:** | Yes | Names of your growing areas. The list starts as **Select Growing Area** |

If any box is empty, the form shows **Enter values for all fields**.

If that area already has a current batch, the form shows **Select a growing area that does not currently have a active batch**.

**Expected result:** The window closes. The new batch appears under **Active Batches** with status **Growing**. The plant date is today.

**Warning:** The **Status:** choice is required, and the batch is still saved as **Growing**. Use **Harvest** or **Terminate** later when you want to change it. See the table below for the stage word you will actually see.

| Stage you pick | Word on the batch card |
| --- | --- |
| **seedling** | **Seedling** |
| **early** | **Seedling** |
| **growth** | **Seedling** |
| **mature** | **Harvest** |

On the card you will see the full batch id, the plant type, the date, the stage word, and **Growing**.

1. Click the arrow to open the batch.
2. Read **Current Growing Area** and **Previous Growing Areas**.

Empty text:

- **Batch is not currently in a growing area**
- **Batch does not have any previous growing areas**

Inside a growing area, the current batch is shortened to the first four characters of the id, with **Type**, **Stage**, **Start Date**, and **End Date**. An open placement shows **N/A** for **End Date**.

### Move a batch

Moving a batch in leafyAI records that the plants now sit in a different growing area. Move the plants yourself as well.

1. Open **Growth & Harvesting**.
2. Open the growing area that holds the batch.
3. On the current batch, click **Edit**. The window title is **Move Batch**.
4. Open **Select Growing Area To Move Batch To:** and choose another area. The list starts as **Select**.
5. Click **Update**, or **Close** to leave it.

[Screenshot: Move Batch window]

**Expected result:** The batch’s current area changes. The old area becomes a previous area, with an end date. The new area shows the batch as current.

| Message | Meaning |
| --- | --- |
| **Select a growing area to move the batch to** | You clicked **Update** before choosing an area |
| **Could not move the batch** | The move was rejected and no more specific message was returned |
| **Destination growing area must be different** | You chose the area the batch is already in |
| **Destination growing area already has a batch move that batch first** | The destination already has a current batch. Move or end that batch first |
| **Batch is not currently in the provided growing area** | The batch is no longer in the area you started from |
| **Select a farm in the navigation bar.** | No farm is selected |

Only one current batch can sit in a growing area at a time.

### Harvest or end a batch

Use this when the crop is picked, or when you are ending it early.

1. On **Active Batches**, click **Edit**.
2. Click **Yes** next to **Edit existing batch:**. The title reads **Edit Batch**.
3. Open **Select Batch To Edit:** and choose the batch id. Only batches with status **Growing** are listed. If the list is empty, the label says **No active batches to edit, create one first...**
4. Click **Harvest** or **Terminate**.

There is no second confirmation.

| Button | Status you will see | Stage you will see | Where the batch goes |
| --- | --- | --- | --- |
| **Harvest** | **Ready** | **Harvest** | **Archived Batches**, and **Previous batches** on the growing area |
| **Terminate** | **Terminated** | The stage stays as it was | **Archived Batches**, and **Previous batches** on the growing area |

The current placement gets an end date. The growing area is free for a new batch.

**Expected result:** The batch leaves **Active Batches**. It remains visible under **Archived Batches**. **Completed Batches** does not increase, because that card looks for the word completed, and these batches are labelled **Ready** or **Terminated**.

**Common mistakes**

- Looking for a harvested crop under **Active Batches**. Open **Archived Batches**.
- Expecting **early** or **growth** to stay written that way. Both show as **Seedling**.
- Trying to harvest a batch that is already **Ready** or **Terminated**. It is not in the edit list.

### Review sensor history

Use **History**, then **Sensor history**, to see how readings changed.

[Screenshot: Sensor history]

1. Select a farm.
2. Click **History**.
3. Click **Sensor history** if it is not already highlighted. It is the default tab.
4. Open the first list and choose **1h**, **24h**, **7d**, or **custom**. **24h** is selected when you arrive.
5. Open the second list and choose **default**, **5m**, **15m**, or **1h**. This is how the readings are grouped.
6. Click sensor names to include or exclude them. A highlighted name is included. If you arrived from a reading card, that sensor starts highlighted. With none highlighted, the chart includes the sensors the page loaded.
7. For **custom**, set **Start**. Set **End** as well when you want an end time.

**Expected result:** Each chosen sensor shows a small chart, the latest value and unit, the time, **min**, **max**, and **n** (how many samples are in that point).

| Message | Meaning |
| --- | --- |
| **Choose a start time for a custom range.** | **custom** is selected and **Start** is empty. The chart waits |
| **No readings in this range.** | The request worked and there were no samples |
| **Select a farm to load history.** | No farm is selected |

**The date and time picker**

1. Click the **Start** or **End** button. Before a date is chosen, it says **Choose date**.
2. Click **Prev** or **Next** to change month.
3. Click a day.
4. Type **Hour** (00 to 23) and **Minute** (00 to 59). The value is kept when you leave the box.
5. Click **Clear** to empty the field.

Weekday headings are **Mo**, **Tu**, **We**, **Th**, **Fr**, **Sa**, and **Su**. If the AI settings have loaded, the time zone name appears above the field.

Sensor names you can click, when the farm has them:

| Button | Reading |
| --- | --- |
| **Temperature** | Air temperature, °C |
| **Humidity** | Relative humidity, % |
| **pH** | Water pH |
| **EC** | Electrical conductivity. The unit on screen is uS/cm |
| **Water Level** | Reservoir level, cm |
| **Water temperature** | Water temperature, °C |
| **Dew point** | Dew point, °C |

### Review individual readings

Use **Readings** when you want a table of single measurements rather than a chart.

1. On **History**, click **Readings**.
2. Click sensor names to limit the table. Click again to clear that limit.
3. Click **valid**, **unverified**, or **suspect** to limit by quality. You can select more than one.
4. Set **Start** and **End** if you want a time window.
5. Read the table. Columns are **Sensor**, **Value**, **Quality**, and **Measured**.
6. Use **Previous** and **Next** to move through pages. The page shows 20 rows at a time. The left side says how many results, for example `20 results`. The middle says the page, for example `1 / 3`.

**Expected result:** Matching rows appear. If none match, the page says **No readings match these filters.** If no farm is selected, it says **Select a farm to load readings.**

### Review camera pictures

Use **Cameras** on **History** to browse saved pictures.

[Screenshot: Camera gallery]

1. On **History**, click **Cameras**.
2. Click a camera name to limit the gallery to that camera.
3. Click **PASS**, **WARN**, **FAIL**, or **UNKNOWN** to limit by image quality.
4. Set **VLM ready** to **any**, **true**, or **false**.
5. Set **Used by AI** to **any**, **true**, or **false**.
6. Set **Start** and **End** if you want a time window.
7. Click a picture to download it to your computer.

Each picture shows the camera name, the capture time, the quality word, and **used by AI** when a recommendation run used it.

The gallery shows 12 pictures per page, with **Previous**, **Next**, and a result count.

**Expected result:** You can find a frame and save a copy. If none match, the page says **No images match these filters.** If no farm is selected, it says **Select a farm to load images.**

**Image quality words**

| Word | Plain meaning |
| --- | --- |
| **PASS** | The picture passed the technical check and can be offered to the vision assistant. The full sentence is **Image quality passed Camera checks and is suitable for VLM visual input.** |
| **WARN** | The picture has a warning and can still be offered. A strong magenta grow-light cast is a warning of this kind. The sentence starts **Image passed the technical VLM gate with a quality warning:** |
| **FAIL** | The picture was rejected for the vision assistant. The sentence starts **Image rejected for VLM visual input because** and may mention blur, darkness, brightness, low contrast, low resolution, or a lack of normal colour. It ends with **Check camera exposure, focus, resolution, colour mode, or viewing setup.** |
| **UNKNOWN** | The quality is not one of the three words above |

**VLM ready** means the picture may be sent to the vision model. **Not VLM ready** means it may not.

### Review past AI runs

Use **AI decisions** on **History** for the full list. **AI Agent** only keeps the latest run and three recent ones.

1. On **History**, click **AI decisions**.
2. Choose a status: **any status**, **pending**, **running**, **completed**, **failed**, or **skipped**.
3. Choose a trigger: **any trigger**, **manual**, **scheduled**, or **legacy**.
4. Choose an input: **any input**, **llm**, or **vlm**.
5. Set **Start** and **End** if you want a time window.
6. Click a **Run** row to switch between **Details** and **Hide**.

The page shows 20 runs at a time.

**Expected result:** You can filter old runs and open the same detail you see on **AI Agent**. If the farm has no runs, the page says **No recommendation runs yet.** If no farm is selected, it says **Select a farm to load recommendation history.**

---

## Settings and personalisation

### What you can change

Open **Settings**. Four buttons sit under the title:

| Button | What it is for |
| --- | --- |
| **New farm** | Create a farm, or delete the selected one |
| **AI configuration** | Choose the assistant, test it, and set the timetable |
| **Sensor ingestion** | Tell leafyAI where the sensors are, and collect readings |
| **Cameras** | Add, edit, capture, and archive cameras |

[Screenshot: Settings tabs]

leafyAI has no theme switch, no language list, and no notification settings. The time zone on a new farm is **Australia/Melbourne**. The screens do not include a box to change it. It is shown under **Next schedule** on **AI Agent**, and above date fields once settings have loaded.

### Create a farm

1. Click **Settings**.
2. Click **New farm**.
3. Type **Name**. This is required. The box allows 255 characters. Empty name shows **Enter a farm name** in red.
4. Type **Location** if you want one. It is optional and allows 255 characters.
5. Click **Create farm**.

**Expected result:** A window titled **Farm created** opens. The first lines are:

**This farm has a controller, standard sensors, and levels 1 and 2. Add the endpoint details before it can collect data.**

The window then lists these four points, in these words:

- **Sensor ingest, on this page: enter the water-quality URL and the ambient-sensor URL, then turn ingestion on. Test and Collect stay unavailable until both URLs are set and the switch is on.**
- **Cameras, on this page: add an RTSP camera if this farm should capture images.**
- **Growing areas, on Growth & Harvesting: levels 1 and 2 exist, and trays and batches are added there.**
- **AI, on this page: the schedule is off and the provider is the mock default. Set a real provider and turn the schedule on if this farm should produce recommendations.**

Click **Close**. The new farm becomes the selected farm. The name and location boxes are cleared.

If creation fails, the red text is the server message, or **Could not create the farm**.

**Tip:** Two farms may use the same name. Pick carefully in the farm list.

### Delete a farm

**Warning:** This is permanent for that farm’s records.

1. Select the farm in the farm list.
2. Open **Settings**, then **New farm**.
3. Click **Delete selected farm**. This button is hidden until a farm is selected.
4. Read **Delete** followed by the farm name and a question mark.
5. Read **This removes the controller, levels, growing areas, cameras, and sensor history for this farm.**
6. Click **Delete farm**, or **Cancel**.

**Expected result:** The window closes and the farm disappears from the list. If deletion fails, red text shows the server message, or **Could not delete the farm**.

### AI configuration

Use this before you turn on a timetable or a real model.

[Screenshot: AI configuration]

1. Select a farm.
2. Open **Settings**, then **AI configuration**.
3. Under **LLM**, choose a provider and type a model name.
4. Under **VLM**, do the same for the vision model.
5. Set **Maximum image age (minutes)**.
6. Turn **Schedule enabled** on if you want automatic runs.
7. If the schedule is on, set the extra boxes.
8. Click **Save settings**.

| Provider name in the list | When to use it |
| --- | --- |
| **mock** | Try the assistant without an outside service. A new farm starts here. The starting model names are **mock-llm** and **mock-vlm** |
| **openrouter** | Use an online model service. Put its key in the key box |
| **ollama** | Use a model hosted on a computer you can reach. Use the key box if that service asks for one |

| Field | Limit | Rule |
| --- | --- | --- |
| **LLM model** | 255 characters | Hint text is **model name** |
| **Replacement LLM API key** | 255 characters | Hidden like a password. Hint is **Optional**, or **Leave blank to keep stored key** when a key is already stored |
| **VLM model** | 255 characters | Hint text is **model name** |
| **Replacement VLM API key** | 255 characters | Same hint rules as the LLM key |
| **Maximum image age (minutes)** | Up to 5 digits | Whole number from 1 to 10080. A new farm uses 60. Error: **Image age must be between 1 and 10080 minutes.** |
| **Schedule enabled** | On or off | Off on a new farm. Extra boxes appear only when it is on |
| **Frequency (minutes)** | Up to 4 digits | Whole number from 1 to 1440. A new farm uses 30. Error: **Interval must be between 1 and 1440 minutes.** |
| **Maximum images** | 1 digit | Whole number from 1 to 8. A new farm uses 4. Error: **Image limit must be between 1 and 8.** |
| **Active start** | 5 characters, `HH:MM` | 24-hour time. A new farm uses `08:00`. Error: **Start time must be 24-hour HH:MM.** |
| **Active end** | 5 characters, `HH:MM` | 24-hour time. A new farm uses `20:00`. Error: **End time must be 24-hour HH:MM.** If it matches the start: **Start and end times must differ.** |

When a key is stored, you see **Stored key** and a masked value, plus **Clear stored LLM key** or **Clear stored VLM key**. Clicking clear marks the key for removal. Click **Save settings** to store that change. When no key is stored, you see **No LLM key stored.** or **No VLM key stored.**

**Expected result:** Green text says **Settings saved.** A red line is the error. If nothing changed, **Save settings** does nothing and shows no message.

**Test the connection**

1. Save the settings you want to test.
2. Click **Test LLM** or **Test VLM**.
3. Read the line under the buttons.

**Expected result:** A successful test shows the provider, the model, and a short reply, separated by slashes and a colon. A failed test shows the server’s reason, or **Provider test failed.**

**Test VLM** needs a farm picture that the quality check will allow. If none exists, the error includes **A reliable readable farm image is required.**

**Tip:** Leave the schedule off until **Test LLM** succeeds. Runs only happen inside **Active start** and **Active end**, and then only every **Frequency (minutes)**. Outside that window, **Next schedule** can say **Outside window**.

### Sensor ingestion

Sensor ingestion is how leafyAI fetches numbers from the two sensor web addresses on your network.

[Screenshot: Sensor ingestion]

1. Select a farm.
2. Open **Settings**, then **Sensor ingestion**.
3. Find the controller card. A new farm’s card title is **Controller**, with the short name **controller** underneath.
4. Turn **Enabled** on when you want collection to run.
5. Type **Water quality URL**. This is the address for pH, EC, and water temperature. The hint is `http://192.168.1.20/readings`. Up to 500 characters.
6. Type **Ambient sensor URL**. This is the address for air temperature, humidity, dew point, and water level. The hint is `http://192.168.1.21/readings`. Up to 500 characters.
7. Set **Poll interval (seconds)**. Whole number from 1 to 86400. The box allows 6 digits. A standard setup starts at 30.
8. Set **Stale after (seconds)**. Whole number from 1 to 604800. The box allows 7 digits. A standard setup starts at 120. A reading older than this is treated as stale.
9. Click **Save**.

**Expected result:** Green text says **Ingest settings saved.** If you edited a box and have not saved, the card says **Unsaved changes**. If nothing changed, **Save** does nothing.

The card also shows **Last success** with a time or **None**, and **failures** with a count. A previous error is printed on the card. The sentence **Missing sensor-ingest settings** is shown in quiet text. Other errors are shown in red.

**Test** checks the addresses and does not keep the readings.

1. Turn **Enabled** on and save both addresses first.
2. Click **Test**.
3. Read the green line. It starts with **Stored** and a count. A test count is **0** because nothing is kept. It may add **Missing:** and sensor names, or **Invalid:** and sensor names.

**Collect** fetches readings and stores them.

1. Click **Collect**.
2. Read **Collect readings?** and **Collect and store readings from** plus the device name.
3. Click **Collect**, or **Cancel**.

**Expected result:** Green text starts with **Stored** and the number of readings kept.

| Message | Meaning |
| --- | --- |
| **Select a farm to edit ingestion.** | No farm is selected |
| **No sensor ingestion configuration exists for this farm.** | This farm has no sensor setup card |
| **Sensor ingestion is disabled for this device.** | **Enabled** is off. Turn it on, click **Save**, then try **Test** or **Collect** again |
| **A collection is already running for this device.** | Wait, then try again |
| **This action is already running.** | The same kind of “already running” reply |
| **Missing sensor-ingest settings: water_quality_url, ambient_sensor_url** | One or both addresses are empty |
| **Use a literal private LAN IP address (for example http://192.168.1.20/readings).** | The address must be a numeric local address, not a website name |
| **Only HTTP and HTTPS endpoints are allowed.** | Start the address with `http://` or `https://` |
| **Credentials must not be embedded in endpoint URLs.** | Do not put a username or password inside the address |
| **Endpoint URLs must not contain fragments.** | Remove any `#` section from the address |
| **The endpoint must use a private LAN address.** | Use an address on your local network |

**Note:** The **Farm created** window says **Test** and **Collect** stay unavailable until the addresses are set and the switch is on. The buttons are still on the screen. The check happens when you click them, and the messages above appear if the setup is not ready.

While a button is working, its label is replaced by a spinning icon. **Save**, **Test**, and **Collect** on that card share that busy state.

### Cameras

Cameras in leafyAI are network cameras that use RTSP. RTSP is the stream address the farm camera already exposes. You cannot add a webcam from the computer you are browsing on.

[Screenshot: Add camera form]

1. Select a farm.
2. Open **Settings**, then **Cameras**.
3. If you already have cameras, each card shows the name, a schedule word, **Last capture**, **next**, and a quality word.
4. To add one, use the card titled **Add camera**.
5. Fill in the fields.
6. Click **Create camera**.

The note under **Add camera** says: **Only RTSP cameras can be added. Leave both active times blank for 24-hour capture.**

| Field | Required | Starting value | Rule |
| --- | --- | --- | --- |
| **Farm level** | Yes | **Farm level** until you choose | **Level 1** or **Level 2**. Error: **Choose a farm level.** |
| **Name** | Yes | Empty. Hint **Top level** | Up to 255 characters. Error: **Name is required.** |
| **Position** | No | Empty. Hint **front** | Up to 100 characters. A place such as front or rear |
| **IP address** | Yes | Empty. Hint `192.168.1.108` | Up to 64 characters. Error: **IP address is required.** |
| **Interval (minutes)** | Yes | `30` | Whole number of at least 1. Error: **Interval must be at least 1 minute.** |
| **RTSP port** | Yes | `554` | Whole number of at least 1. Error: **RTSP port is required.** |
| **RTSP path** | Yes | `/stream1` | Up to 255 characters. Error: **RTSP path is required.** |
| **Active start** | With end, or both blank | Empty. Hint `06:00` | 24-hour `HH:MM` |
| **Active end** | With start, or both blank | Empty. Hint `22:00` | 24-hour `HH:MM` |

If you set only one of **Active start** and **Active end**, the error is **Active start and end must both be set, or both be blank.** If they are the same minute, the error is **Active start and end must differ.**

A new camera is created already enabled. The **Enabled** switch appears when you edit a camera that already exists. It does not appear on the **Add camera** card.

**Expected result:** Green text says the camera name plus **created.** The camera appears in the list.

**Edit, capture, or archive**

1. Change the fields on an existing camera card.
2. Click **Save**. Success text is the camera name plus **saved.**
3. Click **Capture** to take a picture now.
4. Read **Capture image?** and **Capture an image from** plus the camera name.
5. Click **Capture**, or **Cancel**.

Success text is **Captured image**, the picture number, **for**, and the camera name.

1. Click **Archive** to hide a camera from this list.

**Warning:** **Archive** does not ask you to confirm. The camera leaves the list. Success text is the camera name plus **archived.** Archived cameras are not deleted from past pictures already stored. An archived or disabled camera cannot take a new picture. That error is **Disabled or archived cameras cannot capture.**

Other capture messages:

| Message | Meaning |
| --- | --- |
| **A capture is already running for this camera.** | Wait, then try again |
| **Camera capture did not produce an image.** | The camera answered, and no picture was saved |
| **Camera capture failed:** plus a reason | The camera could not be read. Check the address, port, path, and that the camera is powered |
| **Select a farm to manage cameras.** | No farm is selected |
| **No active cameras.** | None are set up yet, or all are archived |

The small schedule word on a camera card means:

| Word | Meaning |
| --- | --- |
| **due** | A capture is due now |
| **scheduled** | A later capture is planned |
| **outside_window** | The current time is outside **Active start** and **Active end** |
| **disabled** | **Enabled** is off |

---

## Managing your account and data

### What is stored

leafyAI keeps this information for the farms on the system, and shows it on the pages in this manual:

| Information | Where you see it |
| --- | --- |
| Your username | Only while you type it at sign-in. The app does not show a profile page |
| Farm name and location | Farm list, and the forms on **Settings** |
| Sensor readings and their quality | **Farm Overview** and **History** |
| Camera pictures and quality results | **History**, camera cards, and AI run details |
| Growing areas, batches, moves, harvests, and ended crops | **Growth & Harvesting** |
| AI settings, except the full secret key | **AI configuration**. A stored key is masked |
| Recommendation text, safety results, and outlet actions | **AI Agent**, **Awaiting Decisions**, and **History** |
| Whether each outlet is on or off | **Device Control** |

The full API key is not shown again after you save it. You see a mask and the words **Stored key**.

Pictures can be saved one at a time. Click the picture in **Cameras** on **History**, or click a frame inside an AI run. leafyAI does not offer a button to download all readings or all farms as a file.

### Log out

1. On a wide screen, click **Log Out** at the bottom of the left bar.
2. On a narrow screen, open the menu icon and click **Log Out**.

**Expected result:** You return to the sign-in page. The next person on this browser needs a username and password. The farm you last selected on this browser can still be selected after you log in again.

### Password and profile

leafyAI has no profile page, no email address on the account, and no **Forgot password** link.

If you forget the password, ask the person who runs the leafyAI computer. They will need to reset it outside this website.

To change a password you still know, there is no **Change password** button in the app.

### Delete data

| Goal | What to do |
| --- | --- |
| Remove one farm and its controller, levels, areas, cameras, and sensor history | [Delete a farm](#delete-a-farm) |
| Hide a camera from the camera list | **Archive** on that camera. This does not ask you to confirm |
| End a crop record | **Harvest** or **Terminate** |
| Remove an empty growing area | **Delete** on **Edit Growing Areas** |
| Remove your user account | This cannot be done in the website |
| Download one picture | Click the picture |

Deleting a farm does not delete your username.

---

## Troubleshooting

| Problem | Likely cause | What to do |
| --- | --- | --- |
| **Could not connect to backend** | leafyAI is not running, or the browser cannot reach the computer that runs it | Start leafyAI with Docker and leave the terminal open. See [Start leafyAI](#start-leafyai). On that computer, open `http://localhost:5173` |
| **Invalid username or password** on **Log In** | The name or password does not match an account, or the password box failed the form rules first | Check capitals. Password rules are in [Create an account](#create-an-account). Click **Close** on the **Note** box |
| **Invalid username or password** on **Sign Up** | The password is under 8 characters, is too common, is too similar to the username, or the username is already taken | Use 8 to 15 characters with a capital letter, a number, and a symbol. Try a different username |
| **Enter an username** | The username box was empty | Type a username and click **Sign Up** again |
| **Password too short** | Fewer than 6 characters | Use at least 8 characters so the server will accept it |
| **Password needs atleast one capital letter** | No capital letter | Add a capital letter |
| **Password needs atleast one number** | No digit | Add a digit |
| **Password needs atleast one special character** | No symbol | Add a symbol such as `!` |
| **Passwords do not match** | **Confirm Password** differs | Type the same password in both boxes |
| The site jumps back to **Sign Up** | You are signed out, or the saved sign-in could not be renewed | Click **Log In** and sign in again |
| **No farms yet. Create a farm in Settings.** | This system has no farms | Open **Settings** and create one |
| **Select a farm in the navigation bar.** | Farms exist and none is selected | Open the farm list and click a name |
| **Could not load farms** | The farm list request failed | Read any red text, check that you are signed in, and refresh |
| Reading cards show **—** or **missing** | No reading has been stored, or the sensor did not report | Set **Sensor ingestion**, click **Collect**, and check the sensor addresses |
| A card says **stale** | The latest reading is older than **Stale after (seconds)** | Check that **Enabled** is on and that **Poll interval (seconds)** is reasonable. Click **Collect** |
| **Ingestion** says **Off** | Collection is disabled | Turn **Enabled** on and click **Save** |
| **Ingestion** says **None** | Ingestion is not configured | Enter both sensor addresses |
| **Ingestion** says **Error** | The last collection failed | Read the error on the **Sensor ingestion** card |
| **Powerboard offline** or **Device offline** | The app cannot read an on/off state from the power strips | Check that the strips are powered and on the network. The red line under **Device Control** is the detail |
| **E-Stop** shows a red error | One or more outlets did not turn off | Read the message. Check the strips, then try the single switches |
| **No decisions waiting** | The latest run has no notice that passed safety | Open **AI Agent** and read **Latest run**. Safety-blocked and automatic items are described there |
| **No recommendation run exists for this farm yet.** | **Generate now** has never completed for this farm, and the schedule has not run | Click **Generate now**, or turn on **Schedule enabled** |
| **Generate** shows a red error | The model, the key, or the farm data was rejected | Read the sentence. Use **Test LLM**. For vision, capture a picture that can reach **PASS** or an allowed **WARN** |
| **A reliable readable farm image is required.** | **Test VLM** found no usable picture | Capture a clear picture first, or test **LLM** only |
| **Provider test failed.** | The test did not return a success flag | Read the detail on the same line. Check the provider, model name, and key |
| **Image age must be between 1 and 10080 minutes.** | **Maximum image age (minutes)** is outside that range | Type a whole number from 1 to 10080 |
| **Interval must be between 1 and 1440 minutes.** | **Frequency (minutes)** is outside that range | Type a whole number from 1 to 1440 |
| **Image limit must be between 1 and 8.** | **Maximum images** is outside that range | Type 1 to 8 |
| **Start time must be 24-hour HH:MM.** or **End time must be 24-hour HH:MM.** | The clock is not `HH:MM` | Use times such as `08:00` and `20:00` |
| **Start and end times must differ.** | The AI day starts and ends at the same minute | Use two different times |
| **Next schedule** says **Outside window** | The schedule is on, and the current time is outside the active hours | Wait until **Active start**, or widen the hours and click **Save settings** |
| **Avg Batch Age** shows **NaNd** | No batch has status **Growing** | Create a batch, or ignore this card until one is growing |
| **Growing Area Usage** shows **NaN%** | There are no growing areas | Create a growing area |
| **Completed Batches** stays at **0** after harvest | That card counts the word completed. Harvested batches are labelled **Ready** | Look in **Archived Batches** |
| **Enter a farm name** | **Name** was blank | Type a farm name |
| **Could not create the farm** | The server rejected the new farm | Read any extra red text and try again |
| **Could not delete the farm** | Deletion failed | Read the red text in the delete window |
| **Farm level can either be 1 or 2** | **Farm Level** was not 1 or 2 | Type `1` or `2` |
| **slotCount must be at least 1** | **Slot Count** was 0 | Type a whole number of 1 or more |
| **All fields must have a value** | Growing-area **Name** or **Slot Count** is empty | Type both. When editing, type the values again. The boxes are not prefilled |
| **Can't delete this growing area as there is a active batch occupying it. Move or terminate this batch before deleting the growing area** | A batch is still in the area | Move, harvest, or terminate that batch, then delete the area |
| **Enter values for all fields** | A batch field was left empty | Choose a stage, a status, a growing area, and a plant type |
| **Select a growing area that does not currently have a active batch** | That area is occupied | Choose an empty area, or move the current batch |
| **Select a growing area to move the batch to** | **Update** was clicked with no destination | Choose an area in the list |
| **Destination growing area already has a batch move that batch first** | The destination is occupied | Move or end the batch that is already there |
| Stage **early** or **growth** shows as **Seedling** | Those two list items are saved as the seedling stage | Pick **seedling** when you want **Seedling**, or **mature** when you want the card to say **Harvest** |
| **Choose a start time for a custom range.** | Sensor history is set to **custom** and **Start** is empty | Pick a start date |
| **No readings in this range.** | No samples in that window | Widen the range, or click **Collect** on **Sensor ingestion** |
| **No readings match these filters.** | The quality or time filter excluded every row | Click the highlighted filters again to clear them |
| **No images match these filters.** | The camera, quality, or time filter excluded every picture | Clear filters, or capture a new picture |
| **end must be later than start.** | The end of a custom range is not after the start | Set **End** later than **Start** |
| **Disabled or archived cameras cannot capture.** | The camera is off or archived | Turn **Enabled** on and click **Save**, or add a new camera |
| **Camera capture failed:** plus a reason | The stream could not be read | Check **IP address**, **RTSP port**, **RTSP path**, power, and network |
| **Use a literal private LAN IP address (for example http://192.168.1.20/readings).** | A sensor address uses a name, or is not a local numeric address | Use an address like the example |
| **Sensor ingestion is disabled for this device.** | **Enabled** is off | Turn it on, click **Save**, then **Test** or **Collect** |
| A button shows only a spinning icon | The action is still running | Wait. The label returns when it finishes |
| You cannot type more characters | The box is at its limit. The counter shows the limit, such as `15/15` | Shorten the text |

---

## FAQ

**Who is leafyAI for?**  
It is for the person operating the project hydroponic farm: watching sensors, switching outlets, recording crops, and reading assistant advice.

**Do I need an email address?**  
No. Sign-up asks for **Username**, **Password**, and **Confirm Password** only.

**Why does the browser tab say LeafyAi?**  
The product is leafyAI. The browser tab reads **LeafyAi**, and the logo on the page reads **LeafyAI**.

**Can I have more than one farm?**  
Yes. Create each one under **Settings** with **Create farm**, then pick the one you want in the farm list.

**Can another operator see my farm?**  
Yes. Anyone who can log in can open every farm on this system.

**Will the assistant turn on the nutrient pump?**  
It can recommend it. It will not switch **Irrigation Pump**, **pH Doser**, or **EC Doser** by itself. It can switch **Farm Fan**, **Light Level 1**, and **Light Level 2** after a safety check passes. You can switch all six by hand.

**What does E-Stop do?**  
It asks you to confirm, then turns off every controlled outlet.

**Why is a switch faded?**  
The outlet state is not on or off, so leafyAI will not send a new command. The tooltip says **Device offline**. If every switch is in that state, the heading says **Powerboard offline**.

**How often do the numbers refresh?**  
**Farm Overview** refreshes on its own, about every 30 seconds, or at the sensor poll interval when that interval is in use. The countdown says **Next refresh in** and a number of seconds. **AI Agent** also checks for newer runs about every 30 seconds while the browser tab is visible.

**Where did my harvested batch go?**  
It is under **Archived Batches**, with status **Ready**. The **Completed Batches** card does not count it.

**Why does my growth stage say Seedling when I chose early?**  
The list items **early** and **growth** are saved as **Seedling**. **mature** is shown as **Harvest**.

**Can I set the plant date?**  
The plant date is the day you click **Create Batch**.

**Can two batches share one growing area?**  
One current batch per area. Move or end the current batch before you place another.

**How do I save a camera picture?**  
On **History**, open **Cameras**, and click the picture. You can also click a frame inside an AI run.

**What is mock?**  
**mock** is the built-in stand-in assistant. A new farm uses it so you can try **Generate now** before you connect **openrouter** or **ollama**.

**I forgot my password. Where is the reset link?**  
There is no reset link. Ask the person who runs the leafyAI computer.

---

## Glossary

| Term | Meaning |
| --- | --- |
| **Batch** | One planting, with a plant type, a stage, a status, and the areas it has occupied |
| **Controller** | The farm device created with a new farm. Sensor setup is edited on its card |
| **Dew point** | The temperature at which moisture in the air would start to condense |
| **EC** | Electrical conductivity. On this farm it describes how strong the nutrients in the water are |
| **Growing area** | A named zone on level 1 or level 2, with a slot count |
| **Ingestion** | The job that fetches sensor readings from the two local web addresses |
| **LLM** | The assistant mode that uses sensor numbers. On screen this is **LLM** or **LLM fallback** |
| **pH** | How acidic or alkaline the water is |
| **RTSP** | The network stream used by the farm cameras. You enter an IP address, a port, and a path |
| **Stale** | A reading that is older than **Stale after (seconds)** |
| **Suspect** | A reading the sensor marked as doubtful |
| **VLM** | The assistant mode that uses camera pictures and sensor numbers |
| **VLM ready** | The picture passed the technical check well enough to be offered to the vision assistant |

---

## Getting help

**Placeholder:** This product does not publish a support email, phone number, or help desk. Before you hand this manual to operators, replace this paragraph with the name and contact details of the person who runs leafyAI.

Until that is filled in, ask the person who started leafyAI on the lab computer. Have this ready when you ask:

- The page name, such as **Farm Overview** or **Settings**
- The farm name selected in the list
- The exact red message, or the exact **Note** text
- What you clicked just before the message appeared
