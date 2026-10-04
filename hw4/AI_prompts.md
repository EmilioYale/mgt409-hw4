# AI Prompts

## 2026-10-04

## Problem 2 — Analyze the database

> I have a SQLite file at data/campus_customs.db for a campus merch shop. Can you go through evry table in it (at least catalogue, inventory and users) and figure out what each feild is? Then start output/harness.md with a section per table that lists the fields and gives me one line on why each field matters for the shop or the chatbot. I'll keep adding to this file in later steps so keep it easy to extned.

## Problem 3 — Build the website

> I want to build the Campus Customs storefront with React, Vite and TypeScript. It needs a nav bar with Home, Products, About Us, Log in and Create acount. For Home and About Us, take inspiration from the look of yalebulldogblue.com, but write all the copy fresh in a friendly student voice, nothing copied.

> Next, the Products page should show cards from the catalogue table with the image, name, price and a short descripton, and the image paths come from the database. Clicking a card should open a detail page with a big image on one side and the description, price, and sizes with stock on the other. Also add a floating chat panel in the bottom right corner, just a stub for now. Then start a simple FastAPI backend/main.py that serves the products and imagse, since it'll turn into the agent backend later.

## Problem 4 — Create account and login

> Now add accounts. The sign-up form should take first name, last name, email and passwrod (a confirm-password field is optional), and login takes email and password. Save new accounts in the users table with the passwords hashed properly, never plain text.

> Can you check that the seed user test@campuscustoms.yale.edu with password "password" can log in, and that a brnad new account works too? After that, add a section to harness.md that explains whats stored for each user and how the passwords are protected.

## Problem 5 — PydanticAI agent backend

> Time to add the chatbot. Put a PydanticAI agent behind FastAPI and connect it to the chat widgit. backend/main.py should be what Uvicorn runs, with a chat route plus the product and login routes. Split the agent into four files: prompts/prompt.md, agent.py, tools.py and models.py. It should read my API key from the enviroment. I need it to run from backend/ with uvicorn main:app --reload --port 8000.

> Now fill in the content. In prompt.md, give the agent the Campus Customs voice and some basic saftey rules, and in models.py add types for chat replies and product cards. Then add a harness.md section explaining how the front end talks to FastAPI and how the agent loads its prompt and model.

## Problem 6 — Tools for product info and stock

> Give the agent tools that look up a product's description, price, and stock by size straight from the databse. It should never make up prices or quantites, and if a size is out of stock it needs to say so clearly.

> Update prompt.md so the agent actually calls the tools whenver someone asks about price or stock, and add return types for the tools to models.py. In harness.md, list each tool and explain why I picked the fields in the results.

## Problem 7 — Chat search that updates the page

> I want the chat to be able to search the catalogue. If someone asks "what hoodies do you have?", the agent should search and return structred matches, and the front end should render those as product cards with image, name, price and short info.

> The cards that come from the chat have to still open the same detial page as the ones on the products page when clicked, can you make sure that works? Then update prompt.md and harness.md to explian how the results get from the agent to the page.

## Problem 8 — Customer memory

> Let's add memory. For logged-in users, save the chat hisotry in a database table and reload it when they come back. Guests should still be able to chat, but only logged-in users get their history saved. The agent should also know who its talking to (name and email) through deps or tools.

> Now pass the page context along, so if someone's on a prodcut page and asks "do you have this in pink?" the agent knows which product they mean. Then in harness.md explain how history is stored, which customer fields the agent can see, and how the page context is passed.

## Problem 9 — Usability improvements

> I need 4 improvments that actually work in the app: 2 on the fron end (looks or ease of use) and 2 on the agent or backend side (more accurate, safer, faster, cheaper, or a new tool). Can you suggest some good ones that fit this shop?

> Ok, go ahead and implement the four we picked and make sure each one really works in the app, since graders will check. Then write output/usability.md that says what each one is and why it helps shoppers or the business.

## Problem 10 — Style the website

> Please restyle the whole site so it feels like a creative, memorible storefront. I'm thinking about fonts, color pallete, layout hierarchy, some motion, how products are presented, and the feel of the chat panel. Be imaginative, not a generic template. Then write a short, concrete output/design.md about what changed and why it helps customers stay and buy.

## Problem 11 — Site testing

> I need screeshots for testing the app. Please capture three of them: the chat checking stock and price from the database, the dynamic cards showing up after a category question, and one of my usability improvements. Save them in output/app_check_images/, with names like inventory.png.

> Now build output/app_check.html using those screenshots, and it should open just by double-clicking it. Give each check a heading, the screenshot, and 1–2 sentences on what it proves. Link the images with relative paths like app_check_images/inventory.png so they dont break.

## Problem 12 — Audit trail, safety, finish harness

> Add an apend-only output/audit_trail.json that logs the agent's activity: the time, tool used, short args and result, and the stop reson. It should never get wiped, only appended to. Add safety rules to prompt.md too. Then finish harness.md with the model fields and why I chose them, the tools and what they can do, the safety rules, and the specs (loop limits, result caps, which models, and how to run the front and back end).

## Problem 13 — Push to GitHub

> Help me get everything ready to push to a pubic GitHub repo inside an hw4/ folder. The .gitignore needs to exclude .env, the database and the product images, and I need a .env.example with placeholders only. The top level should have AI_prompts.md, requirments.txt, .env.example, .gitignore and README.md, plus frontend/, backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md) and output/ (harness.md, design.md, usability.md, app_check.html, app_check_images/, audit_trail.json). The README should explain how to run both the front and back end after putting the data/ pack in place. Please dobule-check the layout before I submit the URL on Canvas.
