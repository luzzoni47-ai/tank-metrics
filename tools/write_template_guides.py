#!/usr/bin/env python3
"""Write the per-calculator guide copy for the pages that fell back to a category template.

Why this exists
---------------
48 of the 101 calculator pages had no hand-written guide, so gen_tool_pages.py
filled their "What this calculator is for" and "How the maths works" sections
from a category template. Eight real-estate pages therefore carried the same
prose, eight agency pages carried the same prose, and so on. Search Console
shows what that cost: pages with a hand-written guide average a median of 4
impressions, the template pages a median of 0.

This script adds real, distinct copy for the highest-impression template pages.
The text lives in tool_guides.json / tool_guides_hinglish.json, which
gen_tool_pages.py already reads, so nothing about the generator changes.

Copy rules (Sir's brief): Hinglish in roman script, rupees and crores only,
never a dollar sign, technical terms stay in English.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "tools" / "tool_guides.json"
HI = ROOT / "tools" / "tool_guides_hinglish.json"

# --- English guides -------------------------------------------------------
EN_CALCS: dict[str, dict] = {
    "propertyvalue": {
        "what": (
            "A property valuation is an estimate of what a flat, house or plot is worth "
            "today. For most homes the fastest honest way to get there is simple: the area "
            "you are buying, multiplied by the rate the locality is actually trading at per "
            "square foot. Banks, brokers and buyers all start from this number before they "
            "argue about anything else. The rate per square foot is the whole argument - a "
            "1,000 sq ft flat is worth ₹80 lakh on one street and ₹1.6 crore two kilometres "
            "away, and the area never changed. So this calculator asks for the two numbers "
            "that matter and nothing else."
        ),
        "formula": (
            "Property Value = Area (sq ft) × Price per Sq Ft. A 900 sq ft flat at ₹7,500 per "
            "sq ft is ₹67.5 lakh. A 1,400 sq ft flat at ₹11,000 per sq ft is ₹1.54 crore. The "
            "reverse is just as useful: if a broker quotes ₹1.2 crore for a 1,200 sq ft flat, "
            "the rate being asked is ₹10,000 per sq ft, and you can compare that against what "
            "nearby flats actually sold for. That single division is how you catch an "
            "overpriced listing."
        ),
        "when": [
            "You have seen a flat and want to sanity-check the asking price against the going rate per square foot.",
            "You are comparing two localities and want both prices on the same per-square-foot basis.",
            "A broker has quoted a lump sum and you want to see what rate per square foot it implies.",
        ],
        "mistakes": [
            "Using the built-up area when the price is quoted on carpet area. The same flat can be 20% smaller on carpet area, and the rate per square foot then looks higher for no reason.",
            "Taking the asking rate as the market rate. Asking prices sit above what actually closes, sometimes by 10% or more.",
            "Ignoring the floor, the age of the building and the facing, which move the rate even within one building.",
        ],
    },
    "epf": {
        "what": (
            "An EPF calculator adds up the money that quietly builds in your Employees' "
            "Provident Fund account every month and shows what it becomes by the time you "
            "retire. Two people pay into it - you and your employer - and both contributions "
            "earn interest, which is where the surprise comes from. The employee share is 12% "
            "of basic salary, the employer puts in a matching amount, and the balance "
            "compounds year after year. A person who joins at 25 and retires at 58 has paid "
            "in for 33 years, and in the last ten of those the interest alone earns more than "
            "the first twenty years of contributions."
        ),
        "formula": (
            "Yearly addition = (Employee Monthly PF + Employer Monthly PF) × 12, and the "
            "balance grows at the EPF rate compounded annually. If you and your employer "
            "together put in ₹10,000 a month at 8.25%, then after 30 years the corpus is "
            "roughly ₹1.42 crore, of which only about ₹36 lakh is money you actually paid in. "
            "The rest is compound interest, and that gap is the entire reason to start early "
            "rather than to contribute more later."
        ),
        "when": [
            "You want to know what your PF becomes by retirement, before deciding how much more to save elsewhere.",
            "You are switching jobs and want to see what leaving the balance untouched actually earns.",
            "You are comparing PF against NPS, PPF or an equity SIP on a like-for-like basis.",
        ],
        "mistakes": [
            "Adding only your own contribution and forgetting the employer share, which roughly doubles the money going in.",
            "Assuming the interest rate stays fixed. The EPF rate is reviewed every year and has moved between about 8% and 8.5% for a decade.",
            "Ignoring the EPS split - part of the employer's share goes to pension rather than to the PF balance that earns interest.",
        ],
    },
    "propertyroi": {
        "what": (
            "A property ROI calculator answers the question every second-home buyer gets "
            "wrong: what did this flat actually earn me? There are two separate returns and "
            "they are easy to confuse. One is cash - the rent you collected. The other is on "
            "paper - how much the flat's value went up. A property can look like a great "
            "investment on appreciation alone and still have paid you almost nothing in cash, "
            "which matters on the day the tenant leaves or the EMI does not wait. This "
            "calculator shows both together, over the years you actually held it."
        ),
        "formula": (
            "Total gain = (Sale Value − Purchase Price) + Rent collected over the holding "
            "period. ROI = Total gain ÷ Purchase Price × 100, and the annualised figure "
            "spreads that over the years held. A flat bought at ₹60 lakh and sold at ₹85 lakh "
            "after 6 years with ₹1.2 lakh rent a year: the gain is ₹25 lakh plus ₹7.2 lakh, so "
            "₹32.2 lakh on ₹60 lakh, about 54% in total and roughly 7.4% a year. Rental "
            "yield, which is just annual rent ÷ purchase price, is the number to compare "
            "against a fixed deposit."
        ),
        "when": [
            "You own a flat that is rented out and want to know the return you are actually earning.",
            "You are deciding between a second property and a fixed deposit or a debt fund.",
            "You are about to sell and want the full gain, cash plus appreciation, before you agree a price.",
        ],
        "mistakes": [
            "Counting appreciation and ignoring the rent, or the other way round. The two together are the return.",
            "Forgetting the money that went out - stamp duty, registration, brokerage, maintenance and the interest on the loan.",
            "Comparing a 6% rental yield with a 7% fixed deposit without adding the appreciation, which is the whole reason people buy property.",
        ],
    },
    "stampduty": {
        "what": (
            "A stamp duty calculator works out the money you pay the government on the day "
            "you register a property, and it is almost always more than a buyer has "
            "budgeted. Stamp duty is a state tax on the transaction and registration is the "
            "fee to record it in your name; together they add roughly 6% to 8% of the "
            "property value in most states, and in a few they cross 10%. On a ₹80 lakh flat "
            "that is ₹5 lakh to ₹8 lakh, paid in one go, and it cannot be added to the loan. "
            "This calculator shows the two charges and the total you have to carry to the "
            "sub-registrar's office."
        ),
        "formula": (
            "Stamp Duty = Property Value × Stamp Duty Rate, and Registration = Property Value "
            "× Registration Rate. Total cost of buying = Property Value + Stamp Duty + "
            "Registration. A ₹80 lakh flat in a state charging 6% stamp duty and 1% "
            "registration costs ₹80 lakh + ₹4.8 lakh + ₹80,000, so ₹85.6 lakh on the day. "
            "Some states charge stamp duty on the higher of the agreement value and the "
            "circle rate, so the government's own floor price can push the bill up."
        ),
        "when": [
            "You are about to register a property and want the exact cash you must arrange on that day.",
            "You are comparing two states or two cities and the transaction cost changes your budget.",
            "You are working out the true all-in cost of a purchase, not just the price the seller quoted.",
        ],
        "mistakes": [
            "Budgeting for the price and forgetting the duty, which on a ₹80 lakh flat is several lakh more.",
            "Assuming stamp duty is the same everywhere. It is a state subject and varies by state, by buyer (women sometimes pay less) and by property type.",
            "Forgetting that stamp duty cannot be financed in the home loan, so it has to be your own cash.",
        ],
    },
    "incometax": {
        "what": (
            "An old vs new regime calculator tells you which of India's two income tax "
            "systems takes less from you this year, and the answer changes with almost every "
            "salary. The new regime gives lower slab rates but throws away most deductions. "
            "The old regime has higher rates but lets you subtract 80C, 80D, HRA and home "
            "loan interest before tax is worked out. So the comparison is not really about "
            "rates at all - it is about whether your deductions are large enough to beat the "
            "rate cut. Someone with no investments is almost always better off in the new "
            "regime; someone carrying a big home loan and full 80C is often better off in "
            "the old one."
        ),
        "formula": (
            "Old regime: tax on (Income − Deductions) using the old slabs. New regime: tax on "
            "Income using the new slabs, with almost no deductions. Whichever tax is lower "
            "wins. A plain ₹15 lakh salary with no investments is usually cheaper in the new "
            "regime, because there is nothing much to deduct. Add a ₹2 lakh home loan "
            "interest and a full ₹1.5 lakh of 80C, and the old regime can pull ahead again. "
            "Finding that crossover is what this calculator is for."
        ),
        "when": [
            "Your employer asks you to pick a regime at the start of the year and you do not want to guess.",
            "You have just taken a home loan or started 80C investments and the answer may have changed.",
            "You are comparing two job offers with different salary structures.",
        ],
        "mistakes": [
            "Assuming the new regime is always better because the rates look lower. It is only better when your deductions are small.",
            "Forgetting that the new regime still gives the standard deduction but not 80C, 80D or HRA.",
            "Comparing last year's numbers with this year's slabs. Both regimes and their slabs have changed more than once in the last few years.",
        ],
    },
    "importduty": {
        "what": (
            "An import duty calculator works out what an imported consignment really costs "
            "by the time it clears customs, and the answer is always more than the invoice. "
            "Customs duty is charged first, and then IGST is charged on the value plus the "
            "duty, so the two compound instead of adding up neatly. A ₹1 lakh shipment at "
            "20% duty and 18% IGST does not cost ₹1.38 lakh; it costs ₹1.42 lakh, because the "
            "IGST is calculated on ₹1.2 lakh and not on ₹1 lakh. On thin import margins that "
            "gap is the difference between a product that sells and one that does not."
        ),
        "formula": (
            "Customs Duty = Product Value × Duty Rate. IGST = (Product Value + Customs Duty) × "
            "IGST Rate. Landed cost = Product Value + Customs Duty + IGST. For ₹1,00,000 at "
            "20% duty: duty is ₹20,000, IGST is 18% of ₹1,20,000 which is ₹21,600, and the "
            "landed cost is ₹1,41,600. Duty rates depend on the HSN code of the product, so "
            "always confirm the exact rate for your item before pricing it."
        ),
        "when": [
            "You are importing goods and want the true cost before you set a selling price.",
            "You are comparing an imported product against a locally made one.",
            "A shipment has landed and the customs bill is higher than you expected, and you want to see why.",
        ],
        "mistakes": [
            "Charging IGST on the product value alone. It is charged on value plus duty, which is why the bill is always bigger than the simple sum.",
            "Using a rough duty rate instead of the exact HSN code rate. The gap between two codes can be more than 10 percentage points.",
            "Forgetting that customs duty is not the only charge - there can be a social welfare surcharge and clearance charges on top.",
        ],
    },
    "gross": {
        "what": (
            "Gross profit is what is left of your sales after you pay for the thing you "
            "sold, and gross margin is that number as a percentage. It is the first profit "
            "line and the most honest one, because nothing is hidden in it. A shop that sells "
            "a product for ₹1,000 that cost ₹600 has ₹400 of gross profit and a 40% gross "
            "margin. That ₹400 is not your profit yet - rent, salaries and marketing still "
            "have to come out of it - but if the 40% is not there in the first place, no "
            "amount of clever cost-cutting later will fix it. Gross margin tells you whether "
            "the business can work at all."
        ),
        "formula": (
            "Gross Profit = Revenue − Cost of Goods Sold. Gross Margin % = (Gross Profit ÷ "
            "Revenue) × 100. Revenue of ₹10 lakh with COGS of ₹6 lakh gives ₹4 lakh of gross "
            "profit and a 40% margin. What counts as healthy depends on the business: "
            "physical products often run 40% to 60%, food 60% to 70%, and software 70% or "
            "more. A D2C brand selling at 25% gross margin is usually in trouble, because the "
            "ad spend alone can eat all of it."
        ),
        "when": [
            "You are pricing a product and want to see what margin the price actually leaves.",
            "You are comparing two products and want to know which one is worth pushing.",
            "You are preparing numbers for an investor and need the first profit line right.",
        ],
        "mistakes": [
            "Calling gross profit your profit. Rent, salaries, marketing and tax still have to come out of it.",
            "Leaving delivery, packaging and payment gateway fees out of COGS. For a D2C brand those are a real part of what the sale costs.",
            "Comparing your margin with a software company's. The same percentage means very different things in different businesses.",
        ],
    },
}

# --- Hinglish guides ------------------------------------------------------
HI_CALCS: dict[str, dict] = {
    "propertyvalue": {
        "what": (
            "Property valuation matlab aaj aapka flat, house ya plot kitne ka hai, iska "
            "estimate. Zyadatar ghar ke liye sabse seedha tareeka yahi hai: area jitna hai, "
            "usse locality ka actual per square foot rate multiply kar do. Banks, brokers aur "
            "buyers sab isi number se shuru karte hain. Asli bahas rate per square foot par "
            "hoti hai - 1,000 sq ft ka flat ek gali mein ₹80 lakh ka hai aur do kilometre "
            "door ₹1.6 crore ka, aur area wahi hai. Isliye yeh calculator sirf do numbers "
            "maangta hai."
        ),
        "formula": (
            "Property Value = Area (sq ft) × Price per Sq Ft. 900 sq ft ka flat ₹7,500 per sq "
            "ft par ₹67.5 lakh. 1,400 sq ft ka flat ₹11,000 per sq ft par ₹1.54 crore. Ulta "
            "bhi kaam ka hai: agar broker 1,200 sq ft ke flat ka ₹1.2 crore maang raha hai, "
            "toh rate ₹10,000 per sq ft ban raha hai - ab isse aas-paas ke actual sold rates "
            "se compare kar lo. Yahi ek division overpriced listing pakad leti hai."
        ),
        "when": [
            "Flat dekh liya aur asking price ko locality ke per square foot rate se check karna hai.",
            "Do localities compare kar rahe ho aur dono ko ek hi per-square-foot basis par laana hai.",
            "Broker ne lump sum bola hai aur aap dekhna chahte ho ki usme rate per square foot kitna nikal raha hai.",
        ],
        "mistakes": [
            "Built-up area use karna jab price carpet area par quote hui ho. Wahi flat carpet par 20% chhota lagta hai aur rate per square foot bina wajah zyada dikhta hai.",
            "Asking rate ko market rate maan lena. Asking prices actual closing se upar hoti hain, kabhi 10% ya zyada.",
            "Floor, building ki age aur facing ignore karna - ye ek hi building ke andar bhi rate badal dete hain.",
        ],
    },
    "epf": {
        "what": (
            "EPF calculator har mahine aapke PF account mein chup-chaap jo paisa jama hota "
            "hai, uska jod lagata hai aur retirement tak woh kitna banega, dikhata hai. Isme "
            "do log daalte hain - aap aur aapka employer - aur dono ka paisa interest kamata "
            "hai, asli chaunkane wali baat yahi hai. Employee share basic salary ka 12% hota "
            "hai, employer utna hi daalta hai, aur balance saal-dar-saal compound hota rehta "
            "hai. Jo 25 par join karke 58 par retire hota hai, usne 33 saal paisa daala hai - "
            "aur aakhri das saal ka interest akela pehle bees saal ki contribution se zyada "
            "hota hai."
        ),
        "formula": (
            "Saalana jama = (Employee Monthly PF + Employer Monthly PF) × 12, aur balance EPF "
            "rate par saalana compound hota hai. Agar aap aur employer milaakar ₹10,000 "
            "mahina daalte ho 8.25% par, toh 30 saal baad corpus takreeban ₹1.42 crore banta "
            "hai - jisme sirf ₹36 lakh woh paisa hai jo aapne actually daala. Baaki compound "
            "interest hai, aur yahi poora reason hai jaldi shuru karne ka, baad mein zyada "
            "daalne ka nahi."
        ),
        "when": [
            "Retirement tak PF kitna banega ye jaan-na ho, isse pehle ki aur kahaan bachana hai woh decide karo.",
            "Job switch kar rahe ho aur dekhna hai ki balance chhedne se kitna nuksan hota hai.",
            "PF ko NPS, PPF ya equity SIP se barabar ki taur par compare karna ho.",
        ],
        "mistakes": [
            "Sirf apni contribution jodna aur employer ka share bhool jaana - isse andar jaane wala paisa takreeban dugna hota hai.",
            "Interest rate fix maan lena. EPF rate har saal review hota hai aur ek dashak se 8% se 8.5% ke beech ghoom raha hai.",
            "EPS split ignore karna - employer ke share ka ek hissa pension mein jaata hai, us PF balance mein nahi jo interest kamata hai.",
        ],
    },
    "propertyroi": {
        "what": (
            "Property ROI calculator us sawaal ka jawab deta hai jo doosra ghar kharidne wala "
            "aksar galat nikalta hai: is flat ne mujhe actually kitna kamaya? Do alag return "
            "hote hain aur dono confuse karna aasan hai. Ek cash hai - jo kiraya aapne liya. "
            "Doosra kagaz par - flat ki value kitni badhi. Sirf appreciation dekhkar property "
            "badi investment lagti hai, par cash mein kuch nahi mila ho sakta - aur tenant "
            "jaane ya EMI rukne par yahi maayne rakhta hai. Yeh calculator dono ek saath "
            "dikhata hai, un saalon ke hisaab se jitne aapne rakha."
        ),
        "formula": (
            "Total gain = (Sale Value − Purchase Price) + holding period ka kul kiraya. ROI = "
            "Total gain ÷ Purchase Price × 100, aur annualised figure isse saalon par baant "
            "deta hai. ₹60 lakh ka flat, 6 saal baad ₹85 lakh par becha, ₹1.2 lakh saalana "
            "kiraya: gain ₹25 lakh plus ₹7.2 lakh = ₹32.2 lakh, ₹60 lakh par - kul takreeban "
            "54%, saalana takreeban 7.4%. Rental yield, matlab saalana kiraya ÷ purchase "
            "price, wahi number hai jise FD se compare karna chahiye."
        ),
        "when": [
            "Flat kiraye par hai aur jaan-na hai ki actually kitna return mil raha hai.",
            "Doosri property aur FD ya debt fund ke beech choose karna hai.",
            "Bechna hai aur price tay karne se pehle poora gain - cash aur appreciation dono - dekhna hai.",
        ],
        "mistakes": [
            "Appreciation ginna aur kiraya bhool jaana, ya ulta. Return dono ko milaakar banta hai.",
            "Jo paisa gaya woh bhool jaana - stamp duty, registration, brokerage, maintenance aur loan ka interest.",
            "6% rental yield ko 7% FD se compare karna bina appreciation jode, jabki log property isi wajah se kharidte hain.",
        ],
    },
    "stampduty": {
        "what": (
            "Stamp duty calculator woh paisa nikalta hai jo property register karne ke din "
            "sarkar ko dena padta hai, aur ye takreeban hamesha budget se zyada hota hai. "
            "Stamp duty transaction par state tax hai aur registration uske naam karane ki "
            "fee; dono milaakar zyadatar states mein property value ka takreeban 6% se 8% ban "
            "jate hain, aur kuch mein 10% se upar. ₹80 lakh ke flat par ye ₹5 lakh se ₹8 lakh "
            "hai, ek saath dena padta hai, aur loan mein add nahi hota. Yeh calculator dono "
            "charges aur woh total dikhata hai jo sub-registrar office le jaana hai."
        ),
        "formula": (
            "Stamp duty = Property Value × Stamp Duty Rate, aur Registration = Property Value "
            "× Registration Rate. Kharidne ki kul cost = Property Value + Stamp Duty + "
            "Registration. ₹80 lakh ka flat, 6% stamp duty aur 1% registration: ₹80 lakh + "
            "₹4.8 lakh + ₹80,000 = us din ₹85.6 lakh. Dhyan rahe, kuch states agreement value "
            "aur circle rate mein se zyada par duty lagati hain, toh sarkar ka apna floor "
            "price bill badha sakta hai."
        ),
        "when": [
            "Property register karne wale ho aur us din ka exact cash pata karna hai.",
            "Do states ya do sheher compare kar rahe ho aur transaction cost budget badal deti hai.",
            "Purchase ki asli all-in cost nikaalni hai, sirf seller ka bataya price nahi.",
        ],
        "mistakes": [
            "Price ka budget rakhna aur duty bhool jaana - ₹80 lakh ke flat par ye kai lakh zyada hota hai.",
            "Stamp duty sab jagah same maan lena. Yeh state subject hai - state, buyer (auraton par kabhi kam) aur property type ke hisaab se badalta hai.",
            "Ye bhool jaana ki stamp duty home loan mein finance nahi hoti, isliye apna cash chahiye.",
        ],
    },
    "incometax": {
        "what": (
            "Old vs new regime calculator batata hai ki is saal India ke do income tax systems "
            "mein se kaunsa aapse kam leta hai - aur jawab lagbhag har salary ke saath badalta "
            "hai. New regime slab rates kam deta hai par zyadatar deductions chheen leta hai. "
            "Old regime ke rates zyada hain par 80C, 80D, HRA aur home loan interest tax se "
            "pehle ghata sakte ho. Isliye comparison rates ka nahi hai - ye dekhna hai ki "
            "aapke deductions rate cut ko beat karte hain ya nahi. Jiske paas investments "
            "nahi, woh lagbhag hamesha new regime mein better hai; jiske paas bada home loan "
            "aur poora 80C hai, woh aksar old regime mein."
        ),
        "formula": (
            "Old regime: (Income − Deductions) par purane slabs se tax. New regime: Income par "
            "naye slabs se tax, lagbhag bina deductions. Jo tax kam, wahi jeeta. Saada ₹15 "
            "lakh salary, koi investment nahi: new regime aksar kam hota hai, kyunki ghata-ne "
            "ke liye zyada kuch hai hi nahi. ₹2 lakh home loan interest aur poora ₹1.5 lakh "
            "80C jodo, toh old regime aage nikal sakta hai. Yahi crossover dhoondhna "
            "calculator ka kaam hai."
        ),
        "when": [
            "Employer saal ke shuru mein regime chunne bolta hai aur guess nahi karna.",
            "Home loan liya ya 80C investments shuru kiye aur jawab badal gaya ho.",
            "Do job offers compare kar rahe ho jinme salary structure alag hai.",
        ],
        "mistakes": [
            "New regime ko hamesha better maan lena kyunki rates kam dikhte hain. Yeh sirf tab better hai jab deductions chhote hain.",
            "Ye bhool jaana ki new regime mein standard deduction milta hai par 80C, 80D ya HRA nahi.",
            "Pichhle saal ke numbers is saal ke slabs se compare karna. Dono regimes aur unke slabs pichhle kuch saalon mein ek se zyada baar badle hain.",
        ],
    },
    "importduty": {
        "what": (
            "Import duty calculator nikalta hai ki customs se clear hone tak ek imported "
            "consignment ki asli cost kitni hoti hai - aur jawab hamesha invoice se zyada "
            "hota hai. Pehle customs duty lagti hai, phir IGST value plus duty par lagti hai, "
            "isliye dono jodne ke bajaye compound ho jaate hain. ₹1 lakh ka shipment, 20% "
            "duty aur 18% IGST: cost ₹1.38 lakh nahi, ₹1.42 lakh hoti hai, kyunki IGST ₹1 "
            "lakh par nahi, ₹1.2 lakh par lagti hai. Patle import margin par yahi gap decide "
            "karta hai ki product bikta hai ya nahi."
        ),
        "formula": (
            "Customs Duty = Product Value × Duty Rate. IGST = (Product Value + Customs Duty) × "
            "IGST Rate. Landed cost = Product Value + Customs Duty + IGST. ₹1,00,000 par 20% "
            "duty: duty ₹20,000, IGST ₹1,20,000 ka 18% = ₹21,600, landed cost ₹1,41,600. Duty "
            "rate product ke HSN code par depend karta hai, isliye price tay karne se pehle "
            "apne item ka exact rate confirm karo."
        ),
        "when": [
            "Import kar rahe ho aur selling price tay karne se pehle asli cost chahiye.",
            "Imported product ko locally bane product se compare kar rahe ho.",
            "Shipment aa gaya aur customs bill expectation se zyada hai - dekhna hai kyun.",
        ],
        "mistakes": [
            "IGST sirf product value par lagana. Yeh value plus duty par lagti hai, isliye bill simple jod se hamesha bada aata hai.",
            "Exact HSN code rate ke bajaye mota-moti duty rate use karna. Do codes ke beech 10 percentage point se zyada ka farq ho sakta hai.",
            "Ye bhool jaana ki customs duty akela charge nahi hai - social welfare surcharge aur clearance charges bhi lagte hain.",
        ],
    },
    "gross": {
        "what": (
            "Gross profit matlab sales mein se jo bacha us cheez ki cost nikalne ke baad jo "
            "aapne bechi, aur gross margin wahi number percentage mein. Yeh pehli profit line "
            "hai aur sabse honest, kyunki isme kuch chhupa nahi hota. Dukaan ₹1,000 ka product "
            "bechti hai jiski cost ₹600 thi, toh gross profit ₹400 aur gross margin 40%. Woh "
            "₹400 abhi aapka profit nahi - kiraya, salary aur marketing isme se nikalna baaki "
            "hai - par agar 40% shuru mein nahi hai, toh baad mein kitni bhi cost-cutting se "
            "fix nahi hoga. Gross margin batata hai ki business chal sakta hai ya nahi."
        ),
        "formula": (
            "Gross Profit = Revenue − Cost of Goods Sold. Gross Margin % = (Gross Profit ÷ "
            "Revenue) × 100. ₹10 lakh revenue aur ₹6 lakh COGS par ₹4 lakh gross profit aur "
            "40% margin. Healthy margin business par depend karta hai: physical products aksar "
            "40% se 60%, food 60% se 70%, software 70% ya zyada. D2C brand jo 25% gross margin "
            "par bech raha hai, woh aksar mushkil mein hai, kyunki akela ad spend poora kha "
            "sakta hai."
        ),
        "when": [
            "Product ki pricing kar rahe ho aur dekhna hai ki price se kitna margin bachta hai.",
            "Do products compare kar rahe ho aur jaan-na hai kaunsa push karne layak hai.",
            "Investor ke liye numbers taiyaar kar rahe ho aur pehli profit line sahi chahiye.",
        ],
        "mistakes": [
            "Gross profit ko apna profit kehna. Kiraya, salary, marketing aur tax abhi isme se nikalna baaki hai.",
            "Delivery, packaging aur payment gateway fees COGS se bahar chhod dena. D2C brand ke liye ye sale ki asli cost ka hissa hain.",
            "Apne margin ko software company se compare karna. Ek hi percentage ka matlab alag business mein bilkul alag hota hai.",
        ],
    },
}

# --- Batch 2 (Hinglish) ---------------------------------------------------
HI_CALCS.update({
    "exitcalc": {
        "what": (
            "Exit calculator dikhata hai ki company bikne par founder ya angel investor ke "
            "haath actually kitna aata hai. News mein jo headline number hota hai woh company "
            "ka price hai; jo aapke bank account tak pahunchta hai woh uska aapka equity "
            "percentage hai, aur dono bilkul alag hain. Agar aapki ₹4.5 crore ki company mein "
            "18% hai, toh payout ₹81 lakh hai - ₹4.5 crore nahi. Founders saalon valuation par "
            "bahas karte hain aur cap table par waqt nahi dete, jabki wahi document us din "
            "yeh number tay karta hai."
        ),
        "formula": (
            "Payout = Exit Valuation × Your Equity %. ₹25 crore ki sale mein 12% hissa ₹3 crore "
            "deta hai. Wahi 12% ₹4.5 crore ki sale mein ₹54 lakh. Asli deals mein do cheezein "
            "chup-chaap isse kam karti hain: sale se thoda pehle banaya gaya ESOP pool, aur "
            "liquidation preference, jisme investors founders se pehle apna paisa le lete hain. "
            "Down-round sale mein preference founder ka payout poora kha sakti hai, chahe "
            "equity percentage kagaz par theek dikhe."
        ),
        "when": [
            "Acquisition offer aaya hai aur jawab dene se pehle apna number chahiye.",
            "Aur raise karna hai ya abhi bechna hai - dono raaste kitna dete hain ye dekhna hai.",
            "Angel investor ho aur diye hue exit par apne stake ka return nikaalna hai.",
        ],
        "mistakes": [
            "Company ka sale price apna payout maan lena. Sirf aapka equity percentage aapka hai.",
            "Liquidation preference bhool jaana - ye investors ko pehle milti hai aur chhoti sale mein founders ko kuch nahi bach sakta.",
            "Aaj se exit tak ki dilution ignore karna - har future round aaj ka percentage chhota kar deta hai.",
        ],
    },
    "moicirr": {
        "what": (
            "MOIC aur IRR wahi do numbers hain jin par venture investor actually deal judge "
            "karta hai. MOIC saada hai: paisa kitne guna wapas aaya. ₹1 daala aur ₹3 mile, "
            "matlab 3x. IRR wahi natija saalana rate mein batata hai, aur yahi number do deals "
            "ko comparable banata hai. Teen saal mein 3x aur das saal mein 3x bilkul ek "
            "achievement nahi hai - pehla takreeban 44% saalana hai, doosra takreeban 12%. Jo "
            "founder ye do numbers bolna seekh jaata hai, usse cheque likhne wale galat nahi "
            "samajhte."
        ),
        "formula": (
            "MOIC = Exit Amount ÷ Investment Amount. IRR woh saalana rate hai jisse investment "
            "exit value tak pahunchta hai: IRR = (Exit ÷ Investment)^(1 ÷ Years) − 1. ₹1 crore "
            "5 saal mein ₹3 crore: 3x MOIC aur takreeban 24.6% IRR. Wahi ₹3 crore 10 saal mein: "
            "3x MOIC par IRR sirf takreeban 11.6%. Investors aksar 3x ya zyada aur 25% ya "
            "behtar chahte hain."
        ),
        "when": [
            "Pitch kar rahe ho aur valuation ke saath-saath round ka return dikhana hai.",
            "Do offers compare kar rahe ho jinke amount aur period alag hain.",
            "Apne investors ko report de rahe ho aur MOIC aur IRR sahi likhna hai.",
        ],
        "mistakes": [
            "Multiple batana par saal nahi. 3x ka koi matlab nahi jab tak period na bolo.",
            "IRR compare karna bina ye note kiye ki IRR maanta hai paisa usi rate par reinvest hota hai, jo aksar nahi hota.",
            "Partial exit par MOIC ko poora picture maan lena - aadha hissa becha toh multiple bhi aadha hi realised hai.",
        ],
    },
    "cpmcpc": {
        "what": (
            "CPM to CPC converter us price ko badalta hai jo aapne hazar impressions ke liye "
            "diya, us price mein jo aapne actually ek click ke liye diya. CPM ad platforms "
            "inventory bechne ka tareeka hai - hazar views ka price. CPC woh hai jo asli log "
            "click karne par padta hai. Dono ke beech ka gap aapka click-through rate hai, aur "
            "yahi ek number campaign ko sasta ya mehnga banata hai. Do campaigns dono ₹200 CPM "
            "par quote ho sakte hain par CPC bilkul alag de sakte hain, kyunki ek creative "
            "click hoti hai aur doosri nahi."
        ),
        "formula": (
            "CPC = (CPM ÷ 1000) × Impressions ÷ Clicks, ya seedha CPM ÷ (CTR% × 10). ₹200 CPM "
            "par 50,000 impressions aur 1,000 clicks: spend ₹10,000, toh CPC ₹10. CTR 4% kar "
            "do toh CPM badle bina CPC aadha ho jaata hai, ₹5. Isliye behtar creative aksar "
            "bade budget se zyada kaam ka hota hai - ye har click ka price kam kar deti hai."
        ),
        "when": [
            "Platform CPM quote kar raha hai aur budget dene se pehle asli cost per click jaanna hai.",
            "Do channels CPM par same lag rahe hain aur CPC par compare karna hai.",
            "Target CPC set kar rahe ho aur uske liye zaroori click-through rate nikaalna hai.",
        ],
        "mistakes": [
            "CPM ko final cost maan lena. Yeh entry price hai, outcome nahi.",
            "Kam CPC ko achha maan lena bina clicks ki quality dekhe. Jo sasta click kabhi convert nahi hota, wahi sabse mehnga hai.",
            "CPM ko per thousand impressions ki jagah per impression maan lena - isse arithmetic 1,000 guna bigad jaata hai.",
        ],
    },
    "cpcpa": {
        "what": (
            "CPC to CPA converter us price ko badalta hai jo aap click ke liye dete ho us price "
            "mein jo customer actually paane ke liye dete ho. CPC ek visit ka price hai; CPA ek "
            "result ka price. Dono ke beech ka pul aapka conversion rate hai, aur aksar sudharne "
            "ka sabse sasta tareeka yahi hota hai. ₹10 CPC aur 2% conversion par customer ₹500 "
            "ka padta hai. Conversion 4% kar do toh wahi customer ₹250 ka - ad, audience ya bid "
            "badle bina."
        ),
        "formula": (
            "CPA = CPC ÷ Conversion Rate. ₹10 per click 2% par ₹500 per acquisition. Wahi ₹10 "
            "5% par ₹200. Ulta karke target set karo: agar 3% conversion par ₹300 tak afford kar "
            "sakte ho, toh ₹9 per click tak bid kar sakte ho. Yahi ek division bid tay karti hai, "
            "guess nahi."
        ),
        "when": [
            "CPC aur conversion rate pata hai aur customer ki asli cost nikaalni hai.",
            "Jo CPA afford kar sakte ho usse maximum bid set karni hai.",
            "Zyaada traffic par kharch karna hai ya landing page convert karana hai - ye decide karna hai.",
        ],
        "mistakes": [
            "CPC ko customer ki cost maan lena. Yeh ek visit ki cost hai, aur zyadatar visits kharidti nahi.",
            "Ad sudharna jab landing page sale gawa raha ho. Leverage aksar conversion rate mein hota hai.",
            "Blended conversion rate use karna jab mobile aur desktop bilkul alag behave karte hain.",
        ],
    },
    "clientltv": {
        "what": (
            "Client lifetime value matlab ek client jaane se pehle kul kitna revenue deta hai, "
            "aur agency ke liye yahi number tay karta hai ki usse paane ke liye kitna kharch kar "
            "sakte ho. ₹40,000 mahina dene wala client jo 18 mahine rukta hai, woh ₹7.2 lakh ka "
            "hai - ₹40,000 ka nahi. Jo agencies har client ko ek mahine ki fee jitna maan kar "
            "price, hiring aur advertising karti hain, woh hamesha cash-starved rehti hain, "
            "kyunki woh rishte ko one-off samajh rahi hain jabki woh dedh saal ki annuity hai."
        ),
        "formula": (
            "LTV = Monthly Revenue × Average Lifetime in months. ₹40,000 mahina, 18 mahine = "
            "₹7.2 lakh. Zyada sahi figure ke liye revenue ki jagah gross margin lo: 60% margin "
            "par wahi client ₹4.32 lakh ka actual profit hai. Asli ratio LTV aur client paane ki "
            "cost ke beech hai - healthy agency LTV ko CAC ka teen guna ya zyada rakhti hai."
        ),
        "when": [
            "Retainer price set kar rahe ho aur rishte ki asli value jaanna chahte ho.",
            "Ek lead ya outbound campaign ke liye kitna de sakte ho ye decide karna hai.",
            "Do client types compare kar rahe ho aur dekhna hai saal mein kaunsa zyada deta hai, mahine mein nahi.",
        ],
        "mistakes": [
            "Revenue ko value kehna. Margin woh hai jo aap rakhte ho, aur zyada revenue wala client jiska delivery cost bhaari ho, sabse kam value wala nikal sakta hai.",
            "Average lifetime guess karna, measure karna nahi. Zyadatar agencies ka anumaan kaafi zyada hota hai.",
            "Churn ignore karna. Agar saal mein chauthai clients jaate hain, average lifetime chaar saal hai, hamesha nahi.",
        ],
    },
    "clientprofit": {
        "what": (
            "Client profitability woh sawaal hai jo agency owner bahut der se poochta hai: team, "
            "tools aur overhead nikalne ke baad, is client ne mujhe paisa banaya ya nahi? ₹2 "
            "lakh mahina ka retainer achha client lagta hai - jab tak us par lage teen log, ad "
            "tools, aur rent-admin ka hissa na gin lo. Bahut agencies ko pata chalta hai ki "
            "unka sabse bada client sabse patla margin hai, aur sabse chhota chup-chaap sabse "
            "profitable. Yeh calculator fee ke saath delivery cost aur overhead rakhta hai."
        ),
        "formula": (
            "Client Profit = Fee − Delivery Cost − Allocated Overhead. Margin % = (Profit ÷ "
            "Fee) × 100. ₹2,00,000 fee, ₹1,30,000 delivery cost aur ₹30,000 allocated overhead "
            "par ₹40,000 bachta hai - 20% margin. Agencies ke liye 40% se 60% healthy hai, 20% "
            "kamzor, aur 15% se neeche client aksar ek late payment door loss se hota hai. "
            "Maksad clients ko nikaalna nahi, jinki price badhani hai unhe dhoondhna hai."
        ),
        "when": [
            "Client list review kar rahe ho aur dekhna hai kaunsa rishta actually paisa deta hai.",
            "Retainer renew karne wale ho aur price tay karne se pehle numbers chahiye.",
            "Naya client unke diye price par lena hai ya nahi ye decide karna hai.",
        ],
        "mistakes": [
            "Overhead chhod dena. Rent, software aur admin asli costs hain aur har client unme hissa rakhta hai.",
            "Sirf woh ghante ginna jo dikhte hain. Agency owner ka apna waqt bhi cost hai, chahe timesheet par na ho.",
            "Low-margin client ko price badhane se pehle nikaal dena. Aksar fix zyada fee hoti hai, khoya client nahi.",
        ],
    },
    "distmargin": {
        "what": (
            "Distributor aur retailer margin calculator dikhata hai ki aap jis price par bechte "
            "ho aur customer jo deta hai, unke beech ka farq chain mein kaise bantta hai. India "
            "mein physical product aksar manufacturer se distributor se retailer se customer tak "
            "jaata hai, aur har stage ko itna margin chahiye ki product shelf par rahe. Agar MRP "
            "har stage check kiye bina set kiya, product push hi nahi hota - distributors aur "
            "retailers chup-chaap woh brand prefer karte hain jo zyada deta hai. Yeh calculator "
            "har step ka margin dikhata hai."
        ),
        "formula": (
            "Distributor Margin % = (MRP − Distributor Price) ÷ MRP × 100, aur Retailer Margin % "
            "= (Distributor Price − Manufacturer Price) ÷ Distributor Price × 100, jis stage ko "
            "measure kar rahe ho uske hisaab se. India mein typical range: distributor 8% se "
            "12%, retailer 15% se 25%. Agar product banane mein ₹60 lagte hain aur MRP ₹100 hai, "
            "toh baantne ke liye ₹40 hain. Distributor ko 10% aur retailer ko 20% do toh aapke "
            "paas ₹30 bachta hai - aur wahi aapka asli margin hai."
        ),
        "when": [
            "Physical product launch kar rahe ho aur aisa MRP set karna hai jisme sabka margin bache.",
            "Distributor keh raha hai margins patle hain aur check karna hai woh sahi hai ya nahi.",
            "Direct online bechna hai ya trade ke through jaana hai - compare karna hai.",
        ],
        "mistakes": [
            "Apni cost se MRP set karna bina trade ke liye jagah chhode, phir hairan hona ki koi stock nahi karta.",
            "Margin galat base par nikaalna - distributor margin aksar MRP par, retailer margin us price par jis par woh kharidta hai.",
            "Ye bhool jaana ki GST iske upar baithta hai aur kisi ke margin ka hissa nahi hai.",
        ],
    },
    "mrpreverse": {
        "what": (
            "MRP reverse calculator pack par chhapi price se shuru karke ulta nikalta hai ki "
            "manufacturer ke roop mein aapko actually kitna milta hai. Yeh direction Indian "
            "founders ko sabse zyada chahiye, kyunki market MRP aapse bahut pehle tay kar deta "
            "hai - competitor ki ₹499 ki bottle wahi price hai jiske saath aapka product baithna "
            "hai. Usse retailer ka cut aur distributor ka cut ghatao, jo bachta hai woh aapka "
            "landing price hai. Agar woh number aapki cost se neeche hai, toh kitni bhi volume "
            "isse theek nahi karegi."
        ),
        "formula": (
            "Landing Price = MRP × (1 − Retailer Margin %) × (1 − Distributor Margin %). ₹500 "
            "MRP, 20% retailer aur 10% distributor margin: ₹500 × 0.80 × 0.90 = ₹360 aapka "
            "landing price. Agar cost of goods ₹300 hai, gross margin ₹60 ya 16.7%. Agar cost "
            "₹380 hai, toh har unit par ₹20 ka loss - aur MRP wahi cheez hai jo badalni padegi."
        ),
        "when": [
            "Product kis price par bikna chahiye ye pata hai aur usme aapka margin kya bachta hai dekhna hai.",
            "Retailer zyada discount maang raha hai aur dekhna hai factory gate par kitna padta hai.",
            "Ek hi product ke do MRP points compare kar rahe ho.",
        ],
        "mistakes": [
            "Dono margins MRP se ek saath ghata dena, ek ke baad ek nahi - doosra margin chhote number par lagta hai.",
            "GST bhool jaana, jo zyadatar cases mein MRP ke bahar hota hai aur aap actually kitna collect karte ho woh badalta hai.",
            "Margins fix maan lena. Alag formats ke retailers ek hi product par bilkul alag cut lete hain.",
        ],
    },
    "areabreakdown": {
        "what": (
            "Built-up area aur carpet area ka farq wahi chhupa hua gap hai jo Indian home buyers "
            "se lakhon le jaata hai. Builders built-up area batate hain kyunki woh bada number "
            "hai; jispar actually furniture rakh sakte ho woh carpet area hai. Farq ko loading "
            "kehte hain, aur flats mein ye aksar 20% se 30% hota hai. 1,200 sq ft built-up aur "
            "25% loading wale flat ka carpet area 900 sq ft hai, aur aap jo per square foot "
            "actually de rahe ho woh brochure ke number se chauthai zyada hai."
        ),
        "formula": (
            "Carpet Area = Built-up Area ÷ (1 + Loading %). 1,200 sq ft built-up, 25% loading: "
            "carpet area 1,200 ÷ 1.25 = 960 sq ft. Ulta karke asli rate dekho: ₹96 lakh ka flat "
            "960 sq ft carpet par usable space ka ₹10,000 per sq ft hai, woh ₹8,000 nahi jo "
            "built-up figure dikhata hai. RERA carpet area disclose karna zaroori karta hai, "
            "isliye agreement ka number hi insist karo."
        ),
        "when": [
            "Do flats compare kar rahe ho aur ek built-up bol raha hai doosra carpet area.",
            "Us space ka asli per-square-foot rate chahiye jo actually use kar sakte ho.",
            "Check karna hai ki agreement brochure ke waade se match karta hai ya nahi.",
        ],
        "mistakes": [
            "Built-up area ko carpet area se seedha compare karna. Dono ek measure nahi hain.",
            "Loading sab jagah same maan lena. Builder, sheher aur project ke hisaab se badalta hai - 20% se kam se 35% se zyada.",
            "Ye bhool jaana ki carpet area khud balcony aur bahari deewarein chhodta hai, isliye usable space aur bhi kam hoti hai.",
        ],
    },
    "downpayment": {
        "what": (
            "Down payment calculator woh cash batata hai jo home loan shuru hone se pehle "
            "jodna padta hai, aur yahi number zyadatar first-time buyers ko rok deta hai. India "
            "mein banks aksar property value ka 75% se 90% tak lend karte hain, toh bache hue "
            "10% se 25% apni jeb se aane chahiye. ₹80 lakh ke flat par 80% loan-to-value par "
            "down payment ₹16 lakh hai - aur ye stamp duty aur registration se pehle, jo loan "
            "mein add hi nahi hoti."
        ),
        "formula": (
            "Down Payment = Property Price × (1 − Loan-to-Value %). ₹80 lakh flat, 80% LTV: "
            "₹16 lakh down aur ₹64 lakh loan. Pehle din jo cash actually chahiye woh zyada hai: "
            "stamp duty aur registration jodo, aksar 6% se 8%, matlab takreeban ₹5 lakh zyada - "
            "kul ₹21 lakh. Lenders LTV agreement value aur valuation report mein se jo kam ho "
            "uspar set karte hain, isliye zyada quoted price hamesha loan nahi badhata."
        ),
        "when": [
            "Property chun li hai aur apply karne se pehle jod-ne wala cash jaanna hai.",
            "Do flats compare kar rahe ho aur ek mein bahut zyada upfront chahiye.",
            "Kharidne se pehle kitna bachana padega ye nikaalna hai.",
        ],
        "mistakes": [
            "Sirf down payment ka budget rakhna aur stamp duty aur registration bhool jaana, jo typical flat par kai lakh jodte hain.",
            "Maanna ki bank poora property price fund karegi. LTV cap valuation par hai, asking price par nahi.",
            "Down payment ke liye poori savings khaali kar dena aur registration, shifting costs ya emergency ke liye kuch na chhodna.",
        ],
    },
    "brokerage": {
        "what": (
            "Brokerage calculator property agent ko dena wala commission nikalta hai, chahe sale "
            "par ya rental agreement par. India mein rate negotiable hai aur sheher aur property "
            "value ke hisaab se badalta hai - sale par aksar transaction value ka 1% se 2%, aur "
            "rental par ek mahine ka kiraya, landlord aur tenant ke beech baanta hua. ₹1.2 crore "
            "ke flat par 1% par brokerage ₹1.2 lakh hai, aur ye deal ke waqt dena padta hai, "
            "loan se nahi."
        ),
        "formula": (
            "Brokerage = Transaction Amount × Commission Rate. ₹1.2 crore sale par 1% = "
            "₹1,20,000. Rental mein brokerage aksar ek mahine ka kiraya hota hai, toh ₹35,000 "
            "mahina ka flat ₹35,000 ka, aksar landlord aur tenant mein barabar baanta hua. Bade "
            "deals par percentage neeche negotiate hota hai - ₹5 crore property par 2% matlab "
            "₹10 lakh, aur zyadatar agents ispar baat karenge."
        ),
        "when": [
            "Kharid ya bech rahe ho aur maan lene se pehle commission jaanna hai.",
            "Kiraye par le rahe ho aur agent ka maanga norm ke against check karna hai.",
            "Do agents alag rates quote kar rahe hain - compare karna hai.",
        ],
        "mistakes": [
            "Rate fix maan lena. India mein brokerage negotiable hai aur sheher ke hisaab se bahut badalta hai.",
            "Ye bhool jaana ki brokerage home loan mein add nahi hoti - ye cash hai, deal par.",
            "Dono taraf se dena bina agreement check kiye. Rental par standard kul ek mahine ka kiraya hai, har taraf se ek nahi.",
        ],
    },
    "cagr": {
        "what": (
            "CAGR woh ek steady saalana rate hai jo business ko shuru se jahaan pahuncha wahan "
            "le jaata, chahe safar kitna bhi utaar-chadhav wala raha ho. Growth batane ka yeh "
            "sabse insaaf wala tareeka hai kyunki isse farq nahi padta ki growth barabar aayi "
            "ya ek achhe saal mein. ₹1 crore se ₹2.5 crore chaar saal mein pahuncha business "
            "takreeban 25.7% saalana badha hai, chahe usne saal ek mein kuch na kiya ho aur saal "
            "chaar mein dugna ho gaya ho. Investors CAGR maangte hain kyunki ye do businesses ko "
            "comparable banata hai."
        ),
        "formula": (
            "CAGR = (Ending Value ÷ Starting Value)^(1 ÷ Years) − 1. ₹1 crore se ₹2.5 crore 4 "
            "saal mein: (2.5)^(1/4) − 1 = 25.7% saalana. Wahi ₹1 crore se ₹2.5 crore 2 saal "
            "mein 58.1% saalana - natija ek, business bilkul alag. Isliye bina time period "
            "wala CAGR bekaar hai."
        ),
        "when": [
            "Investor ko growth report kar rahe ho aur ek imaandar saalana number chahiye.",
            "Apni growth competitor ki growth se alag periods par compare kar rahe ho.",
            "Check karna hai ki projected growth rate aapke business stage ke liye realistic hai ya nahi.",
        ],
        "mistakes": [
            "CAGR ki jagah simple average growth use karna. Achhe aur bure saal ka average aisa number deta hai jo kabhi hua hi nahi.",
            "Bahut chhote period ka CAGR batana. Do saal ki high growth business ke baare mein kuch nahi batati.",
            "Jo number bahut upar-neeche gaya uspar CAGR lagana. Yeh path smooth kar deta hai, jisse ek exceptional saal wale business ki tareef zyada ho jaati hai.",
        ],
    },
    "runrate": {
        "what": (
            "Run rate aapke sabse haal ke mahine ko lekar poochta hai ki agar har mahina waisa hi "
            "ho toh poora saal kaisa dikhega. Yeh tezi se badhte business ko describe karne ka "
            "sabse fast tareeka hai, aur khud ko bewakoof banane ka sabse aasan bhi. ₹25 lakh ka "
            "mahina ₹3 crore ka run rate deta hai, jo serious business lagta hai - jab tak dhyaan "
            "na do ki us mahine mein festive spike tha jo repeat nahi hoga. Run rate direction "
            "batane ke liye kaam ka number hai aur promise ke liye kharab, aur investors farq "
            "jaante hain."
        ),
        "formula": (
            "Annual Run Rate = Last Month's Revenue × 12. ₹25 lakh mahina ₹3 crore saalana. Jis "
            "business mein tez season hota hai, uske liye teen mahine ka average zyada imaandar "
            "hai: ₹25 lakh, ₹18 lakh aur ₹20 lakh ka average ₹21 lakh, toh run rate ₹2.52 crore "
            "hai, ₹3 crore nahi. Steady growth mein monthly figure lo, warna average."
        ),
        "when": [
            "Paisa raise kar rahe ho aur business ka current size batana hai.",
            "Mahine-dar-mahine apni growth track kar rahe ho aur saalana view chahiye.",
            "Apne run rate ko saal ke shuru mein set kiye target se compare karna hai.",
        ],
        "mistakes": [
            "Festive mahine ka run rate saalana figure bana ke pesh karna. Jo monthly trend dekhega woh samajh jaayega.",
            "Lumpy, contract-based revenue wale business par run rate lagana. Yeh us business ki tareef kar deta hai jisme mahine mein ek bada order aaya.",
            "Revenue run rate ko profit run rate samajh lena. ₹3 crore revenue run rate par loss bhi ho sakta hai.",
        ],
    },
    "hra": {
        "what": (
            "HRA exemption calculator nikalta hai ki house rent allowance ka kitna hissa tax se "
            "bachta hai, aur zyadatar salaried log apne haq se kam claim karte hain. Exemption "
            "teen amounts mein sabse chhoti hoti hai: jo HRA actually milta hai, jo kiraya dete "
            "ho minus basic salary ka 10%, aur basic salary ka 50% agar metro mein rehte ho warna "
            "40%. Kyunki sabse chhoti chunti hai, sabse kamzor kadi aapki exemption tay karti hai "
            "- isliye kiraya badhane se exemption sirf ek had tak badhti hai."
        ),
        "formula": (
            "Exemption = inme sabse kam: (1) HRA received, (2) Rent paid − 10% of basic salary, "
            "(3) metro mein basic ka 50% ya warna 40%. Agar basic ₹6 lakh, HRA ₹3 lakh aur "
            "kiraya ₹2.4 lakh: option 2 ₹2.4 lakh − ₹60,000 = ₹1.8 lakh, option 3 metro mein ₹3 "
            "lakh, aur exemption sabse chhoti - ₹1.8 lakh. Dhyan rahe ye sirf old regime mein "
            "chalta hai."
        ),
        "when": [
            "Kiraya dete ho aur filing se pehle jaanna hai kitni exemption claim karni hai.",
            "Old aur new tax regime mein se chun rahe ho aur comparison ke liye HRA figure chahiye.",
            "Salary structure negotiate kar rahe ho aur HRA ki value dekhni hai.",
        ],
        "mistakes": [
            "New regime mein HRA claim karna, jahan ye milta hi nahi.",
            "Poora HRA exempt maan lena. Yeh teen amounts mein sabse chhoti hai, aur rent minus basic ka 10% aksar binding hota hai.",
            "Ye bhool jaana ki family ko kiraya dena sirf tab allowed hai jab kiraya actually diya jaaye aur landlord income declare kare.",
        ],
    },
    "ppf": {
        "what": (
            "PPF calculator dikhata hai ki aapki saalana Public Provident Fund contributions "
            "15 saal ke lock-in mein kya banti hain, aur jawab zyadatar logon ki expectation se "
            "zyada hota hai kyunki PPF tax-free compound hota hai. Aap har saal ek fixed amount "
            "daalte ho, balance par interest milta hai jo poora exempt hai, aur maturity amount "
            "bhi tax-free - isse yeh India ke un gine-chune EEE instruments mein se ek banta hai. "
            "Keemat sabr hai: paisa 15 saal ke liye lock hai, aur yahi poora trade hai."
        ),
        "formula": (
            "Balance PPF rate par saalana compound hota hai har saal ki contribution par, aur "
            "maturity value 15 saal ke ant mein kul hoti hai. ₹1.5 lakh saalana 7.1% par 15 "
            "saal: maturity takreeban ₹40.7 lakh, jisme takreeban ₹22.5 lakh aapki khud ki "
            "contribution hai aur baaki tax-free interest. Financial year mein jaldi daalne se "
            "us paise par poore saal ka interest milta hai, isliye April March se behtar hai."
        ),
        "when": [
            "PPF aur equity SIP ke beech choose kar rahe ho long-term goal ke liye.",
            "Aapki current saalana contribution maturity par kya banti hai ye jaanna hai.",
            "80C deduction ke liye PPF use kar rahe ho aur poora picture dekhna hai, sirf tax saving nahi.",
        ],
        "mistakes": [
            "March ki jagah April mein deposit karna. Us contribution par poore saal ka interest chala jaata hai.",
            "PPF ke 7.1% ko equity fund ke long-run return se compare karna bina ye ginne ki PPF ka return guaranteed aur tax-free hai.",
            "₹1.5 lakh saalana cap bhool jaana, jise ek account mein badhaya nahi ja sakta.",
        ],
    },
})

# --- Batch 2: the rest of the >=50% clusters ------------------------------
EN_CALCS.update({
    "exitcalc": {
        "what": (
            "An exit calculator shows what a founder or an angel investor actually walks "
            "away with when a company is sold. The headline number in the news is the "
            "company's price; the number that reaches your bank account is your equity "
            "percentage of it, and the two are very different. If you own 18% of a company "
            "that sells for ₹4.5 crore, your payout is ₹81 lakh - not ₹4.5 crore. Founders "
            "spend years arguing about valuation and almost no time on the cap table, which "
            "is the document that decides this number on the day it matters."
        ),
        "formula": (
            "Payout = Exit Valuation × Your Equity %. A 12% stake in a ₹25 crore sale pays "
            "₹3 crore. The same 12% in a ₹4.5 crore sale pays ₹54 lakh. Two things quietly "
            "reduce it in real deals: an ESOP pool created just before the sale, and "
            "liquidation preference, where investors take their money back before founders "
            "see anything. In a down-round sale, the preference can wipe a founder's payout "
            "to zero even though the equity percentage still looks healthy on paper."
        ),
        "when": [
            "An acquisition offer has arrived and you want your own number before you reply.",
            "You are deciding whether to raise more or sell now, and need to know what each path pays.",
            "You are an angel investor working out what your stake returns at a given exit.",
        ],
        "mistakes": [
            "Reading the company's sale price as your payout. Only your equity percentage is yours.",
            "Forgetting liquidation preference, which is paid to investors first and can leave founders with nothing in a modest sale.",
            "Ignoring dilution between now and the exit - every future round shrinks the percentage you are using today.",
        ],
    },
    "moicirr": {
        "what": (
            "MOIC and IRR are the two numbers a venture investor actually judges a deal on. "
            "MOIC is simple: how many times the money came back. Put in ₹1 and get ₹3, that "
            "is 3x. IRR is the same outcome expressed as a yearly rate, and it is the number "
            "that makes two deals comparable. A 3x in three years and a 3x in ten years are "
            "not the same achievement at all - the first is roughly 44% a year, the second "
            "about 12%. Founders who learn to speak in these two numbers stop being "
            "misunderstood by the people writing the cheques."
        ),
        "formula": (
            "MOIC = Exit Amount ÷ Investment Amount. IRR is the annual rate at which the "
            "investment grows to the exit value over the years held: IRR = (Exit ÷ "
            "Investment)^(1 ÷ Years) − 1. ₹1 crore becoming ₹3 crore in 5 years is 3x MOIC "
            "and about 24.6% IRR. The same ₹3 crore in 10 years is still 3x MOIC but only "
            "about 11.6% IRR. Investors typically want 3x or more and 25% or better."
        ),
        "when": [
            "You are pitching and want to show the return your round offers, not just the valuation.",
            "You are comparing two offers that return different amounts over different periods.",
            "You are reporting to your own investors and need to state MOIC and IRR correctly.",
        ],
        "mistakes": [
            "Quoting a multiple without the years. A 3x means nothing until you say over how long.",
            "Comparing IRR across deals without noting that IRR assumes money is reinvested at the same rate, which is rarely true.",
            "Using MOIC on a partial exit and treating it as the full picture - if only half the stake was sold, the multiple is only half-realised.",
        ],
    },
    "cpmcpc": {
        "what": (
            "A CPM to CPC converter turns what you paid for a thousand impressions into what "
            "you actually paid for one click. CPM is how ad platforms sell inventory - the "
            "price per thousand views. CPC is what that costs you in practice once real people "
            "start clicking. The gap between the two is your click-through rate, and it is the "
            "single number that decides whether a campaign is cheap or expensive. Two "
            "campaigns can both be quoted at ₹200 CPM and deliver wildly different CPCs, "
            "because one creative gets clicked and the other does not."
        ),
        "formula": (
            "CPC = (CPM ÷ 1000) × Impressions ÷ Clicks, which simplifies to CPM ÷ (CTR% × 10). "
            "At ₹200 CPM with 50,000 impressions and 1,000 clicks: spend is ₹10,000, so CPC is "
            "₹10. Double the click-through rate to 4% and the CPC halves to ₹5 with no change "
            "in CPM. That is why a better creative is usually worth more than a bigger budget - "
            "it lowers the price of every click you buy."
        ),
        "when": [
            "A platform quotes you a CPM and you want to know the real cost per click before you commit budget.",
            "Two channels look similarly priced on CPM and you want to compare them on CPC.",
            "You are setting a target CPC and working backwards to the click-through rate you need.",
        ],
        "mistakes": [
            "Comparing CPM across platforms as if it were the final cost. It is the entry price, not the outcome.",
            "Reading a low CPC as good without checking the quality of the clicks. Cheap clicks that never convert are the most expensive kind.",
            "Forgetting that CPM is per thousand impressions, not per impression, which throws the arithmetic off by a factor of 1,000.",
        ],
    },
    "cpcpa": {
        "what": (
            "A CPC to CPA converter takes what you pay for a click and turns it into what you "
            "pay to actually acquire a customer. CPC is the price of a visit; CPA is the price "
            "of a result. The bridge between them is your conversion rate, and it is usually "
            "the cheapest thing to improve. At a ₹10 CPC and a 2% conversion rate, a customer "
            "costs ₹500. Improve the conversion rate to 4% and the same customer costs ₹250 - "
            "with no change in the ad, the audience or the bid."
        ),
        "formula": (
            "CPA = CPC ÷ Conversion Rate. ₹10 per click at 2% conversion gives ₹500 per "
            "acquisition. The same ₹10 at 5% gives ₹200. Flip it to set a target: if you can "
            "afford ₹300 per customer at a 3% conversion rate, you can bid up to ₹9 per click. "
            "That single division is how you decide a bid instead of guessing at it."
        ),
        "when": [
            "You know your CPC and conversion rate and want the true cost of a customer.",
            "You are setting a maximum bid from the CPA you can afford.",
            "You are deciding whether to spend more on traffic or on making the landing page convert better.",
        ],
        "mistakes": [
            "Treating CPC as the cost of a customer. It is the cost of a visit, and most visits do not buy.",
            "Improving the ad when the landing page is what loses the sale. Conversion rate is where the leverage usually is.",
            "Using a blended conversion rate when mobile and desktop behave completely differently.",
        ],
    },
    "clientltv": {
        "what": (
            "Client lifetime value is the total revenue one client brings you before they "
            "leave, and for an agency it is the number that decides how much you can afford "
            "to spend winning them. A client paying ₹40,000 a month who stays 18 months is "
            "worth ₹7.2 lakh - not ₹40,000. Agencies that price, hire and advertise as if "
            "every client is worth one month's fee are permanently cash-starved, because they "
            "are spending as though the relationship is a one-off when it is actually a "
            "year-and-a-half annuity."
        ),
        "formula": (
            "LTV = Monthly Revenue × Average Lifetime in months. ₹40,000 a month for 18 "
            "months is ₹7.2 lakh. For a truer figure, use gross margin instead of revenue: at "
            "a 60% margin the same client is worth ₹4.32 lakh of actual profit. The ratio that "
            "matters is LTV against the cost of acquiring the client - a healthy agency aims "
            "for LTV at three times CAC or better."
        ),
        "when": [
            "You are setting a retainer price and want to know what the relationship is actually worth.",
            "You are deciding how much you can pay for a lead or an outbound campaign.",
            "You are comparing two client types and want to know which is worth more over a year, not a month.",
        ],
        "mistakes": [
            "Using revenue and calling it value. Margin is what you keep, and a high-revenue client with heavy delivery cost can be the least valuable one you have.",
            "Guessing the average lifetime instead of measuring it. Most agencies overestimate how long clients stay by a wide margin.",
            "Ignoring churn. If a quarter of clients leave each year, the average lifetime is four years, not forever.",
        ],
    },
    "clientprofit": {
        "what": (
            "Client profitability answers the question an agency owner asks too late: after "
            "paying the team, the tools and the overhead, did this client actually make me "
            "money? A ₹2 lakh a month retainer feels like a good client until you count the "
            "three people on it, the ad tools, and the share of rent and admin it consumes. "
            "Many agencies discover their biggest client is their thinnest margin, and their "
            "smallest is quietly the most profitable. This calculator puts the delivery cost "
            "and the overhead next to the fee."
        ),
        "formula": (
            "Client Profit = Fee − Delivery Cost − Allocated Overhead. Margin % = (Profit ÷ "
            "Fee) × 100. A ₹2,00,000 fee with ₹1,30,000 of delivery cost and ₹30,000 of "
            "allocated overhead leaves ₹40,000, a 20% margin. For agencies, 40% to 60% is "
            "healthy, 20% is fragile, and below 15% the client is usually one late payment "
            "away from being a loss. The point of the exercise is to find the clients to raise "
            "prices for, not to fire them."
        ),
        "when": [
            "You are reviewing the client list and want to see which relationships actually pay.",
            "You are about to renew a retainer and want the numbers before you agree a price.",
            "You are deciding whether to take on a new client at the price they are offering.",
        ],
        "mistakes": [
            "Leaving overhead out. Rent, software and admin are real costs and every client carries a share of them.",
            "Counting only the hours you can see. An agency owner's own time is a cost even when it is not on a timesheet.",
            "Firing the low-margin client before trying a price increase. Often the fix is a higher fee, not a lost client.",
        ],
    },
    "distmargin": {
        "what": (
            "Distributor and retailer margin calculator shows how the difference between what "
            "you sell at and what the customer pays is split down the chain. In India a "
            "physical product usually moves manufacturer to distributor to retailer to "
            "customer, and each stage needs enough margin to keep the product on the shelf. "
            "If you set the MRP without checking each stage, the product simply does not get "
            "pushed - distributors and retailers quietly prefer the brand that pays them more. "
            "This calculator shows the margin at every step."
        ),
        "formula": (
            "Distributor Margin % = (MRP − Distributor Price) ÷ MRP × 100, and Retailer Margin "
            "% = (Distributor Price − Manufacturer Price) ÷ Distributor Price × 100, depending "
            "on which stage is being measured. Typical ranges in India: distributor 8% to 12%, "
            "retailer 15% to 25%. If your product costs ₹60 to make and the MRP is ₹100, there "
            "is ₹40 to share. Giving the distributor 10% and the retailer 20% leaves ₹30 to "
            "you, and that is your real margin."
        ),
        "when": [
            "You are launching a physical product and need to set an MRP that leaves everyone a margin.",
            "A distributor says your margins are too thin and you want to check whether they are right.",
            "You are comparing selling direct online against going through the trade.",
        ],
        "mistakes": [
            "Setting the MRP from your own cost without leaving room for the trade, then wondering why nobody stocks it.",
            "Calculating margins on the wrong base - distributor margin is usually on MRP, retailer margin on the price they buy at.",
            "Forgetting that GST sits on top of all of this and is not part of anyone's margin.",
        ],
    },
    "mrpreverse": {
        "what": (
            "An MRP reverse calculator starts from the printed price on the pack and works "
            "backwards to find what you as the manufacturer actually receive. This is the "
            "direction Indian founders need most, because the market sets the MRP long before "
            "you do - your competitor's ₹499 bottle is the price your product has to sit next "
            "to. From there you subtract the retailer's cut and the distributor's cut, and what "
            "is left is your landing price. If that number is below your cost, no amount of "
            "sales volume fixes it."
        ),
        "formula": (
            "Landing Price = MRP × (1 − Retailer Margin %) × (1 − Distributor Margin %). An "
            "MRP of ₹500 with a 20% retailer margin and a 10% distributor margin gives ₹500 × "
            "0.80 × 0.90 = ₹360 as your landing price. If your cost of goods is ₹300, your "
            "gross margin is ₹60, or 16.7%. If the cost is ₹380, you lose ₹20 on every unit "
            "sold, and the MRP is the thing that has to change."
        ),
        "when": [
            "You know the price your product must sell at and need to check the margin that leaves you.",
            "A retailer asks for a deeper discount and you want to see what it costs you at the factory gate.",
            "You are comparing two MRP points for the same product.",
        ],
        "mistakes": [
            "Subtracting both margins from the MRP at once instead of one after the other - the second margin applies to a smaller number.",
            "Forgetting GST, which sits outside the MRP in most cases and changes what you actually collect.",
            "Assuming the margins are fixed. Retailers in different formats take very different cuts for the same product.",
        ],
    },
    "areabreakdown": {
        "what": (
            "Built-up area versus carpet area is the quiet gap that costs Indian home buyers "
            "lakhs. Builders quote the built-up area because it is the bigger number; what you "
            "can actually put furniture on is the carpet area. The difference is called "
            "loading, and it is typically 20% to 30% for flats. A flat sold as 1,200 sq ft "
            "built-up with 25% loading has a carpet area of 900 sq ft, and the price per square "
            "foot you are really paying is a quarter higher than the brochure suggests."
        ),
        "formula": (
            "Carpet Area = Built-up Area ÷ (1 + Loading %). A 1,200 sq ft built-up flat with "
            "25% loading has a carpet area of 1,200 ÷ 1.25 = 960 sq ft. Flip it to see the real "
            "rate: a ₹96 lakh flat at 960 sq ft carpet costs ₹10,000 per sq ft of usable space, "
            "not the ₹8,000 the built-up figure implies. RERA requires carpet area to be "
            "disclosed, so the number on the agreement is the one to insist on."
        ),
        "when": [
            "You are comparing two flats and one quotes built-up while the other quotes carpet area.",
            "You want the true per-square-foot rate on the space you can actually use.",
            "You are checking whether the agreement matches what the brochure promised.",
        ],
        "mistakes": [
            "Comparing a built-up area with a carpet area directly. They are not the same unit of measure.",
            "Assuming loading is the same everywhere. It varies by builder, city and project, from under 20% to over 35%.",
            "Forgetting that carpet area itself excludes the balcony and the external walls, so the usable space is smaller still.",
        ],
    },
    "downpayment": {
        "what": (
            "A down payment calculator tells you the cash you must arrange before a home loan "
            "starts, and it is the number that stops most first-time buyers. Banks in India "
            "typically lend 75% to 90% of the property value, so the remaining 10% to 25% has "
            "to come from your own pocket. On a ₹80 lakh flat at an 80% loan-to-value, the "
            "down payment is ₹16 lakh - and that is before stamp duty and registration, which "
            "cannot be borrowed at all."
        ),
        "formula": (
            "Down Payment = Property Price × (1 − Loan-to-Value %). A ₹80 lakh flat at 80% LTV "
            "needs ₹16 lakh down and a ₹64 lakh loan. The cash you actually need on day one is "
            "larger: add stamp duty and registration, usually 6% to 8%, so about ₹5 lakh more, "
            "making it ₹21 lakh. Lenders set the LTV from the lower of the agreement value and "
            "the valuation report, so a high quoted price does not always raise the loan."
        ),
        "when": [
            "You have picked a property and need to know the cash to arrange before applying.",
            "You are comparing two flats and one needs far more upfront than the other.",
            "You are working out how much you need to save before you can buy.",
        ],
        "mistakes": [
            "Budgeting only the down payment and forgetting stamp duty and registration, which add several lakh on a typical flat.",
            "Assuming the bank will fund the full property price. The LTV cap is on the valuation, not the asking price.",
            "Draining your entire savings for the down payment and leaving nothing for registration, shifting costs or an emergency.",
        ],
    },
    "brokerage": {
        "what": (
            "A brokerage calculator works out the commission payable to a property agent, "
            "whether on a sale or on a rental agreement. In India the rate is negotiable and "
            "varies by city and by property value - commonly 1% to 2% of the transaction value "
            "on a sale, and one month's rent on a rental, split between landlord and tenant. "
            "On a ₹1.2 crore flat at 1%, the brokerage is ₹1.2 lakh, and it is payable at the "
            "time of the deal, not out of the loan."
        ),
        "formula": (
            "Brokerage = Transaction Amount × Commission Rate. A ₹1.2 crore sale at 1% is "
            "₹1,20,000. For a rental, brokerage is usually one month's rent, so a ₹35,000 a "
            "month flat costs ₹35,000, often shared equally between landlord and tenant. On "
            "high-value deals the percentage is negotiable downwards - a 2% rate on a ₹5 crore "
            "property is ₹10 lakh, and most agents will discuss that."
        ),
        "when": [
            "You are buying or selling and want to know the commission before you agree to it.",
            "You are renting and want to check what the agent is asking against the norm.",
            "You are comparing two agents quoting different rates.",
        ],
        "mistakes": [
            "Assuming the rate is fixed. Brokerage in India is negotiable and varies widely by city.",
            "Forgetting that brokerage cannot be added to the home loan - it is cash, paid at the deal.",
            "Paying on both sides without checking the agreement. On a rental, the standard is one month's rent in total, not one month from each side.",
        ],
    },
    "cagr": {
        "what": (
            "CAGR is the single steady yearly rate that would take a business from where it "
            "started to where it ended, ignoring how bumpy the ride was. It is the fairest way "
            "to describe growth because it does not care whether the growth came evenly or in "
            "one good year. A business going from ₹1 crore to ₹2.5 crore in four years has "
            "grown at roughly 25.7% a year, even if it did nothing in year one and doubled in "
            "year four. Investors ask for CAGR because it makes two businesses comparable."
        ),
        "formula": (
            "CAGR = (Ending Value ÷ Starting Value)^(1 ÷ Years) − 1. ₹1 crore to ₹2.5 crore "
            "over 4 years: (2.5)^(1/4) − 1 = 25.7% a year. The same ₹1 crore to ₹2.5 crore in "
            "2 years is 58.1% a year - the same outcome, a very different business. That is why "
            "a CAGR without a time period attached is meaningless."
        ),
        "when": [
            "You are reporting growth to an investor and want a single honest yearly number.",
            "You are comparing your growth with a competitor's over different periods.",
            "You are checking whether a projected growth rate is realistic for your business stage.",
        ],
        "mistakes": [
            "Using simple average growth instead of CAGR. Averaging a good year and a bad year gives a number that never actually happened.",
            "Quoting a CAGR over too short a period. Two years of high growth says very little about a business.",
            "Applying CAGR to a number that swung wildly. It smooths the path, which can flatter a business that had one exceptional year.",
        ],
    },
    "runrate": {
        "what": (
            "A run rate takes your most recent month and asks what a full year would look like "
            "if every month were the same. It is the fastest way to describe a business that is "
            "growing quickly, and the easiest way to fool yourself. A ₹25 lakh month gives a ₹3 "
            "crore run rate, which sounds like a serious business - until you notice that "
            "month included a festive spike that will not repeat. Run rate is a useful "
            "direction-of-travel number and a poor promise, and investors know the difference."
        ),
        "formula": (
            "Annual Run Rate = Last Month's Revenue × 12. ₹25 lakh a month gives ₹3 crore a "
            "year. For a business with a strong seasonal peak, a three-month average is more "
            "honest: ₹25 lakh, ₹18 lakh and ₹20 lakh average ₹21 lakh, so the run rate is ₹2.52 "
            "crore rather than ₹3 crore. Use the monthly figure when you are growing steadily "
            "and the average when you are not."
        ),
        "when": [
            "You are raising money and want to state the current size of the business.",
            "You are tracking your own growth month on month and want a yearly view.",
            "You are comparing your run rate against a target you set at the start of the year.",
        ],
        "mistakes": [
            "Presenting a festive-month run rate as if it were the annual figure. Anyone who looks at the monthly trend will see it.",
            "Using run rate for a business with lumpy, contract-based revenue. It flatters a business with one big order in the month.",
            "Confusing revenue run rate with profit run rate. A ₹3 crore revenue run rate can sit on a loss.",
        ],
    },
    "hra": {
        "what": (
            "An HRA exemption calculator works out how much of your house rent allowance "
            "escapes tax, and most salaried people claim less than they are entitled to. The "
            "exemption is the smallest of three amounts: the HRA you actually receive, the "
            "rent you pay minus 10% of basic salary, and 50% of basic salary if you live in a "
            "metro or 40% otherwise. Because it is the smallest of the three, the weakest link "
            "sets your exemption - so raising the rent you pay raises your exemption only up "
            "to a point."
        ),
        "formula": (
            "Exemption = the least of: (1) HRA received, (2) Rent paid − 10% of basic salary, "
            "(3) 50% of basic salary in a metro or 40% elsewhere. If basic salary is ₹6 lakh, "
            "HRA is ₹3 lakh and rent is ₹2.4 lakh: option 2 is ₹2.4 lakh − ₹60,000 = ₹1.8 "
            "lakh, option 3 is ₹3 lakh in a metro, and the exemption is the smallest - ₹1.8 "
            "lakh. Note this works only in the old regime."
        ),
        "when": [
            "You pay rent and want to know how much exemption to claim before filing.",
            "You are choosing between the old and new tax regime and want the HRA figure for the comparison.",
            "You are negotiating a salary structure and want to see what HRA is worth to you.",
        ],
        "mistakes": [
            "Claiming HRA in the new regime, where it is not available at all.",
            "Assuming the full HRA is exempt. It is the smallest of three amounts, and rent minus 10% of basic is often the binding one.",
            "Forgetting that paying rent to a family member is allowed only if the rent is actually paid and the landlord declares the income.",
        ],
    },
    "ppf": {
        "what": (
            "A PPF calculator shows what your yearly Public Provident Fund contributions become "
            "over the 15-year lock-in, and the answer is more than most people expect because "
            "PPF compounds tax-free. You put in a fixed amount each year, the balance earns "
            "interest that is fully exempt, and the maturity amount is tax-free too - which "
            "makes it one of the very few EEE instruments in India. The cost is patience: the "
            "money is locked for 15 years, and that is the whole trade."
        ),
        "formula": (
            "The balance grows at the PPF rate compounded annually on each year's "
            "contribution, and the maturity value is the sum at the end of 15 years. ₹1.5 lakh "
            "a year at 7.1% for 15 years matures at roughly ₹40.7 lakh, of which about ₹22.5 "
            "lakh is your own contributions and the rest is tax-free interest. Contributing "
            "early in the financial year earns interest on that money for the whole year, so "
            "April beats March."
        ),
        "when": [
            "You are deciding between PPF and an equity SIP for a long-term goal.",
            "You want to know what your current yearly contribution becomes at maturity.",
            "You are using PPF for the 80C deduction and want to see the full picture, not just the tax saving.",
        ],
        "mistakes": [
            "Depositing in March instead of April. You lose a full year's interest on that contribution.",
            "Comparing the 7.1% PPF rate with an equity fund's long-run return without accounting for the fact that PPF's return is guaranteed and tax-free.",
            "Forgetting the ₹1.5 lakh yearly cap, which cannot be exceeded in a single account.",
        ],
    },
})


# --- Batch 3: the remaining 26, so no page is left on a template -------
EN_CALCS.update({
    "percent": {
        "what": ("A percentage calculator answers the single most common money question: "
                 "what is X% of this number, and if the result is this, what percentage is "
                 "that? Every discount, every tax rate, every growth figure and every margin "
                 "is a percentage underneath, so this is the tool the rest of the site is "
                 "built on. The trap is that percentages do not add up the way people expect - "
                 "a 20% rise followed by a 20% fall does not leave you where you started, it "
                 "leaves you 4% down."),
        "formula": ("Percentage of a number = Number × Percentage ÷ 100. A 15% discount on "
                    "₹2,400 is ₹360 off, so you pay ₹2,040. Reverse it: if ₹2,040 is what you "
                    "paid after 15% off, the original is 2,040 ÷ 0.85 = ₹2,400. And the change "
                    "between two numbers is (New − Old) ÷ Old × 100, which is how you check "
                    "whether that 'huge' rise is actually big."),
        "when": ["You are checking a discount or a tax amount on a bill.",
                 "You want to know by what percentage a number went up or down.",
                 "You are working out a margin or a share of a total."],
        "mistakes": ["Adding and subtracting percentages as if they were plain numbers. They compound, and the order matters.",
                     "Calculating a rise from the new number instead of the old one. The base changes the answer.",
                     "Treating percentage points and per cent as the same thing. Going from 4% to 6% is a 2 percentage point rise but a 50% increase."],
    },
    "markup": {
        "what": ("Markup and margin are two ways of describing the same profit, and mixing "
                 "them up is one of the most expensive small mistakes in business. Markup is "
                 "the profit as a percentage of your cost. Margin is the profit as a "
                 "percentage of your selling price. So markup is always the bigger number on "
                 "the same sale. A trader who thinks in markup but quotes a margin to a "
                 "distributor can find themselves pricing 20% below what they intended."),
        "formula": ("Markup % = (Selling Price − Cost Price) ÷ Cost Price × 100. Margin % = "
                    "(Selling Price − Cost Price) ÷ Selling Price × 100. Buy at ₹600, sell at "
                    "₹1,000: the profit is ₹400, which is a 66.7% markup but only a 40% margin. "
                    "That gap is why a '40% margin' product is not a '40% markup' product, and "
                    "confusing the two can cost you real money on a big order."),
        "when": ["You are pricing a product and want to state the profit both ways correctly.",
                 "A buyer asks for a margin and you want to convert it into the price you must charge.",
                 "You are comparing your pricing with a competitor's and want a like-for-like number."],
        "mistakes": ["Quoting markup as margin to a buyer, which makes your prices look higher than they are.",
                     "Working out a selling price by adding the margin to the cost, when a margin is a share of the selling price.",
                     "Forgetting that both numbers shrink the moment you offer a discount, because the selling price changed."],
    },
    "breakeven": {
        "what": ("A break-even point is the exact sales volume at which a business stops losing "
                 "money and starts making it. Below it every sale still leaves you short of your "
                 "fixed costs; at it the rent, salaries and bills are covered; above it each "
                 "extra unit contributes. It is the first number a lender or an investor "
                 "actually wants, because it tells them how much room there is between the "
                 "business's current sales and disaster."),
        "formula": ("Break-Even Units = Fixed Costs ÷ (Selling Price − Variable Cost). Fixed "
                    "costs of ₹2,00,000 a month, a product selling at ₹500 with ₹300 of variable "
                    "cost, leaves ₹200 contribution per unit, so break-even is 1,000 units. In "
                    "rupees that is 1,000 × ₹500 = ₹5,00,000 of revenue a month. Raise the price "
                    "or cut the variable cost and the break-even falls - that is the whole lever."),
        "when": ["You are setting a monthly sales target and want the floor, not the aspiration.",
                 "You are deciding whether to take on fixed costs like a shop or a hire.",
                 "A lender or investor has asked how much you need to sell to stop losing money."],
        "mistakes": ["Leaving some fixed costs out of the calculation, which makes break-even look far closer than it is.",
                     "Using gross revenue instead of contribution - what matters is what each unit leaves after its own variable cost.",
                     "Treating break-even as a profit target. At break-even you make nothing; it is the point where the losses stop."],
    },
    "ccc": {
        "what": ("The cash conversion cycle is how many days your money is stuck in the "
                 "business between paying for stock and getting paid by customers. A business "
                 "can be profitable on paper and still run out of cash, and this is usually "
                 "why. You buy inventory, hold it, sell it on credit, and only then collect. "
                 "Every day in that chain is a day your money is working for someone else. "
                 "Cutting the cycle is often faster than growing sales."),
        "formula": ("CCC = Days Inventory + Days Receivables − Days Payables. If stock sits "
                    "for 60 days, customers take 45 days to pay, and you pay suppliers in 30 "
                    "days, the cycle is 60 + 45 − 30 = 75 days. That means 75 days of costs "
                    "have to be funded from somewhere - usually your own pocket or a loan. "
                    "Negotiating 45-day supplier terms instead of 30 cuts the cycle to 60 days "
                    "with no extra sales at all."),
        "when": ["You are profitable but constantly short of cash and want to see where it is stuck.",
                 "You are negotiating payment terms with a supplier or a large customer.",
                 "You are planning how much working capital you need before the busy season."],
        "mistakes": ["Measuring the cycle on the best customer and not the average one. One slow payer can carry the whole number.",
                     "Extending payables to improve the ratio without noticing that suppliers then raise prices or stop supplying.",
                     "Confusing profit with cash. A profitable business with a 90-day cycle can still fail."],
    },
    "depreciation": {
        "what": ("Straight-line depreciation spreads the cost of an asset evenly across the "
                 "years you expect to use it. A machine costing ₹10 lakh that will last ten "
                 "years costs the business ₹1 lakh a year, whether or not you spend anything "
                 "that year. It is not a cash payment - it is the accounting way of matching "
                 "the cost of the asset to the years that benefit from it, and it is what makes "
                 "the profit figure honest."),
        "formula": ("Yearly Depreciation = (Asset Cost − Salvage Value) ÷ Useful Life. A "
                    "₹10,00,000 machine with a ₹1,00,000 resale value over 10 years depreciates "
                    "at (10,00,000 − 1,00,000) ÷ 10 = ₹90,000 a year. After four years the book "
                    "value is ₹10,00,000 − ₹3,60,000 = ₹6,40,000. For tax, the Income Tax Act "
                    "uses written-down value blocks instead, so the accounting figure and the "
                    "tax figure differ - your accountant reconciles the two."),
        "when": ["You are preparing accounts and need the yearly charge for an asset.",
                 "You are comparing buying equipment against renting it, and the true yearly cost matters.",
                 "You want to know what an asset is still worth on the books."],
        "mistakes": ["Treating depreciation as cash leaving the business. It is a non-cash charge and the money was spent when you bought the asset.",
                     "Using a useful life that is too long to make profits look better - the asset then breaks before it is written off.",
                     "Forgetting that tax depreciation follows the Income Tax Act's rates, not your own estimate."],
    },
    "gst": {
        "what": ("A GST calculator does the two things you need constantly: adds GST to a price "
                 "to get the final bill, and pulls GST out of an amount that already includes "
                 "it. The second direction is the one that catches people, because a price "
                 "quoted as inclusive of GST hides a smaller base than it looks. In India the "
                 "rate is split into CGST and SGST for sales inside a state, or a single IGST "
                 "for sales across states, but the total is the same."),
        "formula": ("GST Amount = Base Price × GST Rate ÷ 100, and the final price is Base + "
                    "GST. A ₹1,000 base at 18% has ₹180 of GST and a ₹1,180 bill. Reverse it: "
                    "if a bill is ₹1,180 inclusive of 18% GST, the base is 1,180 ÷ 1.18 = "
                    "₹1,000 and the tax is ₹180. The reverse direction uses division, not "
                    "subtraction - subtracting 18% from ₹1,180 gives ₹967.60, which is wrong."),
        "when": ["You are raising an invoice and need the GST amount and the total.",
                 "A price is quoted as inclusive and you need the base and the tax separated.",
                 "You are comparing a GST-inclusive price with a GST-exclusive one."],
        "mistakes": ["Subtracting the GST rate from an inclusive price instead of dividing by (1 + rate). It always understates the base.",
                     "Forgetting that GST is charged on the discounted price when a discount is given before supply, but on the full price when it is given afterwards.",
                     "Treating GST collected as your money. It is held for the government and has to be paid."],
    },
    "gst_taxwealth": {
        "what": ("This GST calculator handles the slightly messier real-world case: a discount "
                 "is applied first, then GST is charged on what remains, and the tax is split "
                 "into CGST and SGST for you. The order matters. A 10% discount followed by 18% "
                 "GST gives a different answer from 18% GST followed by a 10% discount on the "
                 "gross, and getting it the wrong way round means your invoice does not match "
                 "your books."),
        "formula": ("Discounted Base = Base Amount × (1 − Discount %). GST = Discounted Base × "
                    "GST Rate. Total = Discounted Base + GST, with CGST and SGST each at half "
                    "the rate for an intra-state sale. A ₹10,000 base with 10% discount and 18% "
                    "GST: the base becomes ₹9,000, GST is ₹1,620 split as ₹810 CGST and ₹810 "
                    "SGST, and the invoice total is ₹10,620."),
        "when": ["You are issuing an invoice with a trade discount and GST on top.",
                 "You need the CGST and SGST split for an intra-state sale.",
                 "You are reverse-calculating the base from a GST-inclusive amount you were paid."],
        "mistakes": ["Charging GST on the pre-discount amount. For a discount shown on the invoice, GST applies to the discounted value.",
                     "Splitting the tax evenly when the sale is inter-state - that should be IGST at the full rate, not CGST plus SGST.",
                     "Rounding CGST and SGST separately and letting the total drift by a rupee or two from the invoice."],
    },
    "landed": {
        "what": ("Landed cost is the true total of getting a product into your warehouse, and "
                 "it is almost always higher than the invoice. Manufacturing is only the first "
                 "line - packaging, freight, insurance, customs clearance, and the last-mile "
                 "delivery to your godown all land on the same unit. Founders who price from "
                 "the manufacturing cost alone discover months later that they have been "
                 "selling at a loss, because the number they used was never the real cost."),
        "formula": ("Landed Cost per Unit = (Manufacturing + Packaging + Shipping + Other "
                    "Costs) ÷ Units. A batch of 1,000 units costing ₹4,00,000 to make, ₹40,000 "
                    "to pack, ₹60,000 to ship and ₹30,000 in other charges lands at (4,00,000 + "
                    "40,000 + 60,000 + 30,000) ÷ 1,000 = ₹530 per unit. If you have been pricing "
                    "at ₹500, every sale has been losing ₹30, and that is the whole point of "
                    "calculating this."),
        "when": ["You are setting a selling price and need the true cost of one unit.",
                 "You are comparing a domestic supplier with an imported one.",
                 "You are checking whether a product line is actually making money."],
        "mistakes": ["Pricing from the manufacturing cost and leaving freight and clearance out.",
                     "Spreading one-off costs like tooling across a single batch instead of the volumes it will serve.",
                     "Forgetting that duties and taxes paid on import can be credited back later, so the cash cost and the real cost differ."],
    },
    "discountimpact": {
        "what": ("A discount impact calculator shows what a discount actually costs you, and it "
                 "is far more than the percentage suggests. A 10% discount on a product with a "
                 "40% margin does not cost you 10% of profit - it costs you a quarter of it. "
                 "This is the number founders miss when they offer a 'small' discount to close a "
                 "deal, because the discount comes off the price while the cost stays exactly "
                 "where it was."),
        "formula": ("New Price = Selling Price × (1 − Discount %). New Profit = New Price − Cost "
                    "Price. A product selling at ₹1,000 with a cost of ₹600 has ₹400 profit. A "
                    "10% discount takes the price to ₹900, so profit falls to ₹300 - a 25% drop "
                    "in profit for a 10% discount. To earn back the lost profit you would need "
                    "33% more sales volume, which is why blanket discounts are so rarely worth "
                    "it."),
        "when": ["A customer asks for a discount and you want to know what it really costs.",
                 "You are running a sale and want the volume you need just to break even on it.",
                 "You are comparing a discount against other ways to win the sale."],
        "mistakes": ["Reading the discount as a percentage of profit. It comes off the price, and profit is a much smaller number.",
                     "Giving the discount without working out the extra volume it needs to justify itself.",
                     "Discounting a low-margin product, where the same percentage wipes out most or all of the profit."],
    },
    "homeemi": {
        "what": ("A home loan EMI calculator shows the fixed monthly payment on a housing loan "
                 "and, just as importantly, what the loan costs you in total. An EMI has two "
                 "parts - interest and principal - and in the early years almost all of it is "
                 "interest. That is why a 20-year loan at 8.5% costs far more than the amount "
                 "borrowed, and why a small prepayment in the first few years saves far more "
                 "than the same amount paid later."),
        "formula": ("EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1), where P is the loan amount, r the "
                    "monthly interest rate (annual rate ÷ 12 ÷ 100) and n the number of months. "
                    "A ₹50 lakh loan at 8.5% for 20 years is an EMI of about ₹43,391, and the "
                    "total paid over the term is about ₹1.04 crore - roughly double the loan. "
                    "The same loan over 30 years drops the EMI to about ₹38,446 but raises the "
                    "total cost to about ₹1.38 crore."),
        "when": ["You are comparing loan offers from two banks at different rates and tenures.",
                 "You want to know how much a longer tenure costs you in total interest.",
                 "You are deciding whether to prepay or invest the extra money."],
        "mistakes": ["Choosing the longest tenure for the lowest EMI. The monthly saving is small and the extra interest is large.",
                     "Ignoring that a floating rate means the EMI or the tenure can change, and the total is not fixed.",
                     "Forgetting processing fees, insurance and the stamp duty on the loan agreement, which are not in the EMI."],
    },
    "landunits": {
        "what": ("A land area unit converter turns square feet into the units Indian land is "
                 "actually sold in - square yards, square metres, and the traditional units "
                 "that still rule property deals in many states: guntha, cent, bigha and acre. "
                 "This matters because a plot quoted in one unit and compared against another "
                 "is not a fair comparison, and the traditional units differ from state to "
                 "state, so a bigha in one state is not a bigha in the next."),
        "formula": ("1 square yard = 9 square feet. 1 square metre = 10.764 square feet. 1 acre "
                    "= 43,560 square feet, which is 4,840 square yards. 1 guntha = 1,089 square "
                    "feet, so 40 guntha make an acre. 1 cent = 435.6 square feet, so 100 cents "
                    "make an acre. A 2,400 square feet plot is 266.7 square yards or about 223 "
                    "square metres - useful when the buyer and the seller are quoting different "
                    "units for the same land."),
        "when": ["A plot is quoted in one unit and you need to compare it with another.",
                 "You are reading a sale deed or a 7/12 extract and need the area in a unit you understand.",
                 "You are converting between traditional units and square feet for a listing."],
        "mistakes": ["Assuming a bigha or a guntha is the same everywhere in India. These units vary by state and sometimes by district.",
                     "Mixing up square feet and square yards, which differ by a factor of nine.",
                     "Converting the area but not checking the survey number and boundaries against the deed."],
    },
    "ctc": {
        "what": ("A CTC calculator shows what an employee actually costs the company, which is "
                 "always more than the salary in the offer letter. On top of gross salary the "
                 "employer pays provident fund, and often gratuity, insurance and other "
                 "benefits. For a small business owner this is the number to budget, because "
                 "hiring at ₹50,000 a month costs meaningfully more than ₹50,000 a month. For "
                 "an employee it explains why take-home is smaller than the CTC."),
        "formula": ("Employer Cost = Gross Monthly Salary + Employer PF + Other Monthly "
                    "Benefits, and the yearly figure is twelve times that. A ₹50,000 gross "
                    "salary with a 12% employer PF of ₹6,000 and ₹2,000 of other benefits costs "
                    "₹58,000 a month, or ₹6,96,000 a year. Add gratuity at roughly 4.81% of "
                    "basic and the true annual cost crosses ₹7 lakh - against a CTC that looked "
                    "like ₹6 lakh."),
        "when": ["You are hiring and want the real monthly cost to budget for.",
                 "You are an employee checking why take-home is much lower than CTC.",
                 "You are comparing a full-time hire against a freelancer."],
        "mistakes": ["Budgeting only the gross salary and being surprised by the PF and benefits cost.",
                     "Confusing CTC with take-home. CTC includes employer contributions that never reach the employee's bank account.",
                     "Forgetting gratuity, which accrues every year and is payable at the end of service."],
    },
    "freelance": {
        "what": ("A freelancer hourly rate calculator works out what you must charge per hour "
                 "to reach your target income - and the answer is always higher than freelancers "
                 "first guess. The reason is that a freelancer's billable hours are a fraction "
                 "of the hours worked. Sales, invoicing, learning, admin and gaps between "
                 "projects are all real time that nobody pays for, and a rate set on a 40-hour "
                 "week is a rate that will leave you underpaid."),
        "formula": ("Hourly Rate = Target Monthly Income ÷ Billable Hours per Month. If you "
                    "want ₹1,00,000 a month, work 40 hours a week but only 50% of them are "
                    "billable, and you work 4 weeks, that is 80 billable hours. ₹1,00,000 ÷ 80 "
                    "= ₹1,250 an hour. Charge ₹800 and you will earn ₹64,000, no matter how "
                    "hard you work. The billable percentage is the number freelancers "
                    "consistently overestimate."),
        "when": ["You are quoting a client and want a rate that actually pays you.",
                 "You are moving from a job to freelancing and want to match your old salary.",
                 "You are deciding whether a project at a given price is worth taking."],
        "mistakes": ["Assuming every working hour is billable. Most freelancers bill 50% to 70% of their time at best.",
                     "Setting the rate from a competitor's price instead of from the income you need.",
                     "Forgetting tax, and the fact that you pay your own PF, insurance and holidays."],
    },
    "franchise": {
        "what": ("A franchise or store ROI calculator answers the one question that decides "
                 "whether to open: how long until I get my money back? The upfront cost of a "
                 "store - franchise fee, deposit, fit-out, initial stock - is large and mostly "
                 "sunk, and the monthly profit is what pays it back. An outlet that costs ₹25 "
                 "lakh to open and makes ₹1.5 lakh a month takes about 17 months to pay back, "
                 "and that is the number to compare against the franchise agreement's term."),
        "formula": ("Payback Period in months = Starting Investment ÷ Monthly Profit. A ₹25 "
                    "lakh investment earning ₹1,50,000 a month pays back in about 17 months. "
                    "Return on investment is the yearly profit divided by the investment: "
                    "₹18,00,000 ÷ ₹25,00,000 = 72% a year, which looks excellent until you "
                    "check whether the ₹1.5 lakh is the realistic month or the best month. "
                    "Payback past the agreement's term means the model does not work."),
        "when": ["You are evaluating a franchise offer and want the payback before signing.",
                 "You are comparing two locations with different rents and expected sales.",
                 "You are deciding whether to open a second outlet."],
        "mistakes": ["Using the franchisor's projected sales instead of a conservative figure of your own.",
                     "Leaving working capital out of the investment. The store needs stock and cash before it earns.",
                     "Ignoring the royalty and marketing fees, which come off monthly profit before you see it."],
    },
    "funnel": {
        "what": ("A marketing funnel calculator shows what you pay at every step - per click, "
                 "per lead and per sale - so you can see exactly where the money is leaking. "
                 "Each stage has its own cost, and each stage's cost is the previous one "
                 "divided by its conversion rate. Most businesses know their ad spend and their "
                 "sales and nothing in between, which makes it impossible to tell whether the "
                 "problem is the ad, the landing page or the sales follow-up."),
        "formula": ("CPC = Ad Spend ÷ Clicks. CPL = Ad Spend ÷ Leads. CPA = Ad Spend ÷ "
                    "Conversions. Spend ₹50,000 for 2,500 clicks, 250 leads and 25 sales: CPC "
                    "is ₹20, CPL is ₹200 and CPA is ₹2,000. Now you can see that doubling the "
                    "lead-to-sale rate to 20% halves the CPA to ₹1,000, which is far cheaper "
                    "than trying to halve the CPC."),
        "when": ["A campaign is not profitable and you want to find which stage is failing.",
                 "You are setting targets for CPC, CPL and CPA before launching.",
                 "You are comparing two channels that look similar on ad spend alone."],
        "mistakes": ["Optimising CPC when the leak is further down the funnel. Cheap clicks that never convert are worthless.",
                     "Measuring a channel on its last click when the customer saw three touchpoints first.",
                     "Comparing CPA across channels without checking the quality of the customers each one brings."],
    },
    "saas": {
        "what": ("ARPU, MRR and ARR are the three numbers every subscription or app business "
                 "is judged on. MRR is the recurring revenue you can expect every month, ARR is "
                 "the same annualised, and ARPU is the average revenue per user. Investors look "
                 "at these before almost anything else, because recurring revenue is far more "
                 "valuable than one-off sales - it can be forecast, and it compounds as "
                 "customers stay."),
        "formula": ("MRR = Total Monthly Revenue from subscriptions. ARR = MRR × 12. ARPU = MRR "
                    "÷ Active Users. ₹8,00,000 of monthly subscription revenue is ₹96,00,000 "
                    "ARR. With 2,000 active users the ARPU is ₹400 a month. Two things move "
                    "these numbers: new customers raise MRR, and churn lowers it. A business "
                    "growing MRR while losing 8% of customers a month is filling a leaking "
                    "bucket."),
        "when": ["You are raising money and need to state MRR and ARR correctly.",
                 "You are comparing two pricing plans and want to see which raises ARPU.",
                 "You are tracking whether growth is real or just offsetting churn."],
        "mistakes": ["Counting one-off setup fees or annual prepayments as MRR. Only recurring revenue belongs in it.",
                     "Reporting ARR from a single good month instead of the current run rate.",
                     "Watching ARPU without watching churn. Higher ARPU with high churn still shrinks the business."],
    },
    "agencycac": {
        "what": ("Client acquisition cost is what your agency spends to win one client, and it "
                 "is the number that decides how much you can afford to spend on marketing. It "
                 "is not just ad spend - it includes the salesperson's cost, the pitches that "
                 "went nowhere, and the tools used to find and follow up leads. An agency "
                 "spending ₹5 lakh a quarter to win 10 clients has a CAC of ₹50,000, and if "
                 "those clients are worth ₹2 lakh over their life, the maths works."),
        "formula": ("CAC = (Marketing Spend + Sales Cost) ÷ New Clients. ₹4,00,000 of marketing "
                    "and ₹1,00,000 of sales cost to win 10 clients is a CAC of ₹50,000. Compare "
                    "it with client lifetime value: if LTV is ₹2,00,000, the ratio is 4 to 1, "
                    "which is healthy. Below 3 to 1 the agency is spending too much to grow, "
                    "and every new client makes the cash position worse before it gets better."),
        "when": ["You are setting a marketing budget and want to know what a client can cost you.",
                 "You are comparing paid channels against referrals and outbound.",
                 "You are checking whether growth is actually profitable."],
        "mistakes": ["Counting only ad spend and leaving the sales salary and tools out.",
                     "Dividing by all leads instead of clients actually won.",
                     "Comparing CAC with one month's fee instead of the client's full lifetime value."],
    },
    "agencymargin": {
        "what": ("Agency profit margin is what is left of your revenue after delivery and "
                 "operating costs, and agencies are famous for confusing revenue with profit. "
                 "A ₹1 crore agency with ₹95 lakh of costs is a ₹5 lakh business, not a ₹1 "
                 "crore one. The two biggest leaks are delivery cost - the team time each "
                 "client consumes - and the overhead that grows quietly as the agency does: "
                 "more tools, a bigger office, more admin."),
        "formula": ("Profit Margin % = (Revenue − Total Costs) ÷ Revenue × 100. Revenue of "
                    "₹1,00,00,000 with ₹95,00,000 of costs leaves ₹5,00,000, a 5% margin. For a "
                    "services agency, 20% to 30% is healthy and 40% is excellent. The fastest "
                    "fix is usually price, not cost: a 10% price rise on the same cost base "
                    "takes that 5% margin to 14.5%, which no amount of tool-cutting can match."),
        "when": ["You are reviewing the year and want to know what the agency actually earned.",
                 "You are setting next year's pricing and want to know the margin you need.",
                 "You are comparing a month against the same month last year."],
        "mistakes": ["Calling revenue profit. The two are wildly different in an agency.",
                     "Leaving the owner's own salary out of the cost base, which flatters the margin.",
                     "Cutting tools and software when the real problem is that the work is priced too low."],
    },
    "churn": {
        "what": ("Churn rate is the percentage of clients or customers you lose in a period, "
                 "and it is the number that quietly decides whether a business grows or runs to "
                 "stand still. Losing 5% of clients a month does not sound serious until you "
                 "realise it means losing almost half of them in a year. Churn also caps your "
                 "growth: if you lose 8 clients a month and win 8, you are working hard to stay "
                 "exactly where you are."),
        "formula": ("Churn Rate % = Clients Lost ÷ Clients at Start × 100. Losing 6 of 120 "
                    "clients is 5% monthly churn. Annualised, roughly 46% of the base is gone "
                    "in a year. To actually grow by 10 clients a month you must win 16, because "
                    "6 are leaving. Reducing churn from 5% to 3% is often worth more than "
                    "doubling new sales, and it is cheaper, because the clients are already "
                    "yours."),
        "when": ["You are reviewing client retention and want the honest monthly figure.",
                 "You are setting a sales target and need to know how much of it churn will eat.",
                 "You are deciding whether to invest in retention or acquisition."],
        "mistakes": ["Measuring churn yearly and missing that the monthly figure compounds.",
                     "Counting a client as retained because the contract exists, even though they have stopped using the service.",
                     "Reporting revenue churn when the question was customer churn - one large client leaving moves the two very differently."],
    },
    "breakevenad": {
        "what": ("Break-even ad spend is the most you can pay for advertising before a campaign "
                 "stops making money. It is the ceiling, not a target, and it is set by your own "
                 "margin - not by what competitors bid or what a platform suggests. A product "
                 "with ₹300 of contribution per sale can afford to spend almost all of that to "
                 "win the sale and still break even, but every rupee above it is a loss. Knowing "
                 "this number stops you from bidding your way into a loss."),
        "formula": ("Contribution per Sale = Revenue per Sale − Product Cost per Sale. "
                    "Break-Even Ad Spend = Contribution per Sale × Expected Conversions. Sell at "
                    "₹1,000 with a product cost of ₹600 and the contribution is ₹400. Expecting "
                    "20 conversions, you can spend up to ₹8,000 and break even - an ₹8,000 ad "
                    "budget, or a maximum cost per acquisition of ₹400. Spend ₹10,000 and the "
                    "campaign loses ₹2,000."),
        "when": ["You are setting a maximum bid or a daily ad budget.",
                 "A campaign is running and you want to know when to switch it off.",
                 "You are comparing two products and want to see which can support more ad spend."],
        "mistakes": ["Using revenue instead of contribution. The product cost has to come out before ad spend is affordable.",
                     "Treating break-even as the target. At break-even you make nothing; you need to spend below it.",
                     "Forgetting delivery, packaging and payment fees, which reduce the contribution and therefore the ceiling."],
    },
    "pitchscore": {
        "what": ("A Shark Tank pitch check runs your numbers against the questions the sharks "
                 "actually ask, and tells you which ones are likely to get you grilled. On "
                 "Shark Tank India the interrogation is remarkably consistent: what is your "
                 "valuation and why, what are your revenue and margins, what does it cost to "
                 "get a customer, and how many months of cash do you have left? A pitch that "
                 "has clean answers to those four is a pitch that survives the room."),
        "formula": ("There is no single formula - the check looks at ratios. Valuation against "
                    "revenue shows how expensive the ask is. LTV against CAC shows whether "
                    "growth is profitable; below 3 to 1 the sharks push back. Runway in months "
                    "shows how much time the business has. Gross margin shows whether the "
                    "product can fund its own growth. A ₹10 crore valuation on ₹1 crore of "
                    "revenue is a 10x multiple, and the pitch has to justify it."),
        "when": ["You are preparing a pitch and want to know your weak numbers first.",
                 "An investor has asked for your metrics and you want to sanity-check them.",
                 "You are deciding what to fix before you raise."],
        "mistakes": ["Walking in with a valuation and no revenue to support it. The multiple is the first thing questioned.",
                     "Not knowing your CAC and LTV when asked, which reads as not knowing your own business.",
                     "Quoting a burn rate that implies a short runway without a plan for it."],
    },
    "lovefun": {
        "what": ("A love calculator is a bit of fun - it takes two names, runs them through a "
                 "letter-based formula and returns a compatibility percentage. It is not "
                 "psychology, astrology or anything else with a claim behind it, and it should "
                 "not be read as advice about a relationship. It exists because people enjoy "
                 "it, and a calculator site should have a few tools that are just entertainment. "
                 "Tank Metrics labels it as entertainment on purpose."),
        "formula": ("The score comes from counting how often the letters of the two names "
                    "appear in the phrase 'loves', weighting the totals, and reducing the result "
                    "to a percentage. There is no science in it - the same two names always "
                    "give the same number, which is the only consistency it has. Treat the "
                    "output as a party trick, not a prediction."),
        "when": ["You want a light-hearted answer for a group chat.",
                 "You are curious what the same two names score more than once.",
                 "You want something quick and harmless to share."],
        "mistakes": ["Taking the result seriously. It is entertainment and nothing more.",
                     "Reading anything into a low score. There is no basis for it.",
                     "Using it to make any decision about a real relationship."],
    },
    "babyname": {
        "what": ("A baby name number calculator turns the letters of a name into a number "
                 "using the same letter-values used in numerology, and shows what that number "
                 "is traditionally associated with. Many Indian families look at this when "
                 "choosing a name, alongside the rashi and the nakshatra. It is a tradition "
                 "rather than a science, and Tank Metrics presents it that way - useful as one "
                 "input among several, not as a rule."),
        "formula": ("Each letter is given a value from 1 to 9 in the Chaldean or Pythagorean "
                    "system, the values are added, and the digits are reduced until a single "
                    "digit from 1 to 9 remains - unless the total is 11, 22 or 33, which are "
                    "kept as they are. The name 'Aarav' becomes 1 + 1 + 2 + 1 + 6 = 11, which "
                    "is one of the master numbers and is not reduced further."),
        "when": ["You are choosing between two name spellings and want to compare their numbers.",
                 "You are curious what number a name reduces to.",
                 "You want a traditional input alongside the rashi and nakshatra."],
        "mistakes": ["Treating the number as a hard rule for choosing a name. It is a tradition, not a requirement.",
                     "Getting different answers by spelling the name differently, and not realising the spelling is what changed the number.",
                     "Ignoring the rashi and the family's own preferences because of the number alone."],
    },
    "compatibility": {
        "what": ("A compatibility calculator compares two names with a playful scoring "
                 "formula and returns a percentage. It is the same idea as the love calculator "
                 "with a different method - letters are matched, counted and reduced to a score. "
                 "There is no claim behind it and no evidence for it. It is a fun tool, and the "
                 "site says so plainly rather than dressing it up as insight."),
        "formula": ("The two names are matched letter by letter, common letters are counted and "
                    "weighted, and the total is reduced to a percentage out of 100. The same "
                    "pair of names always produces the same result, which is the only "
                    "predictable thing about it. A high score is no more meaningful than a low "
                    "one - both are arithmetic on letters."),
        "when": ["You want a quick, playful answer to share.",
                 "You are curious how two names score against each other.",
                 "You want a light-hearted tool, not an assessment."],
        "mistakes": ["Reading the score as a real measure of compatibility between people.",
                     "Drawing any conclusion about a relationship from it.",
                     "Assuming a different spelling would not change the answer - it would."],
    },
    "daysbetween": {
        "what": ("Days between two dates counts the calendar days from one date to another, "
                 "which sounds trivial until you need it. It is used to work out notice "
                 "periods, invoice due dates, interest accrual, project timelines and the days "
                 "left before a deadline. It counts calendar days, not working days, so a "
                 "30-day notice period spans weekends and holidays too - which is why a "
                 "'one-month' notice is often more than 30 days."),
        "formula": ("Days = End Date − Start Date, counted as calendar days. From 1 April to 30 "
                    "April is 29 days, not 30, because the start date is not counted. From 15 "
                    "January to 15 March in a non-leap year is 59 days. For a due date, add the "
                    "credit period to the invoice date: a 45-day term on a 1 March invoice falls "
                    "due on 15 April."),
        "when": ["You are checking a notice period or a contract deadline.",
                 "You are working out when an invoice actually falls due.",
                 "You are planning a project timeline and need the number of days."],
        "mistakes": ["Counting the start date as day one, which adds a day to every answer.",
                     "Confusing calendar days with working days. Only the first includes weekends and holidays.",
                     "Forgetting that February changes length in a leap year, which shifts every date after it."],
    },
    "bmi": {
        "what": ("A BMI calculator estimates body mass index from height and weight, giving a "
                 "rough indication of whether an adult is underweight, in the normal range, "
                 "overweight or obese. It is a screening tool, not a diagnosis: it does not "
                 "distinguish muscle from fat, and it is not designed for children, pregnant "
                 "women, or very muscular people. In India the healthy range is adjusted "
                 "downwards, because the risk of diabetes and heart disease rises at a lower "
                 "BMI than it does in Western populations."),
        "formula": ("BMI = Weight in kilograms ÷ (Height in metres)². Someone weighing 70 kg at "
                    "1.70 m: 70 ÷ (1.70 × 1.70) = 70 ÷ 2.89 = 24.2. The standard WHO ranges are "
                    "under 18.5 underweight, 18.5 to 24.9 normal, 25 to 29.9 overweight and 30 "
                    "plus obese. For Indians, health authorities often treat 23 as the upper "
                    "end of normal, so a BMI of 24.2 is a caution rather than a clean bill of "
                    "health."),
        "when": ["You want a quick general indication of where your weight sits for your height.",
                 "You are tracking a change over time rather than reading a single number.",
                 "You want to know the Indian-adjusted range, which is lower than the WHO one."],
        "mistakes": ["Treating BMI as a diagnosis. It is a screening estimate and misses muscle, bone density and body composition.",
                     "Using the WHO range for an Indian adult, where the healthy ceiling is lower.",
                     "Applying it to children or pregnant women, for whom BMI is not the right measure at all."],
    },
})

HI_CALCS.update({
    "percent": {
        "what": ("Percentage calculator us sabse aam money sawaal ka jawab deta hai: is number "
                 "ka X% kitna hai, aur agar result itna hai toh woh kitne percent hai? Har "
                 "discount, har tax rate, har growth figure aur har margin andar se percentage "
                 "hi hai, isliye poori site isi tool par khadi hai. Jaal ye hai ki percentages "
                 "jodte nahi jaise log sochte hain - 20% badhne ke baad 20% gire toh aap wahi "
                 "nahi rehte, 4% neeche rehte ho."),
        "formula": ("Number ka percentage = Number × Percentage ÷ 100. ₹2,400 par 15% discount "
                    "₹360 hai, toh aap ₹2,040 dete ho. Ulta: agar 15% off ke baad ₹2,040 diye, "
                    "toh original 2,040 ÷ 0.85 = ₹2,400 hai. Aur do numbers ke beech badlav = "
                    "(New − Old) ÷ Old × 100, isse pata chalta hai ki woh 'bada' rise actually "
                    "bada hai ya nahi."),
        "when": ["Bill par discount ya tax check kar rahe ho.",
                 "Jaanna hai koi number kitne percent badha ya ghata.",
                 "Margin ya kisi total ka hissa nikaal rahe ho."],
        "mistakes": ["Percentages ko simple numbers ki tarah jodna-ghatana. Ye compound hote hain, aur order maayne rakhta hai.",
                     "Naye number se rise nikaalna purane se nahi. Base badalne se jawab badal jaata hai.",
                     "Percentage points aur per cent ko same samajh lena. 4% se 6% jaana 2 percentage point ka rise hai par 50% ka increase."],
    },
    "markup": {
        "what": ("Markup aur margin ek hi profit ko batane ke do tareeke hain, aur inhe mix kar "
                 "dena business ki sabse mehngi chhoti galtiyon mein se ek hai. Markup profit "
                 "hai aapki cost ka percentage. Margin profit hai aapke selling price ka "
                 "percentage. Isliye ek hi sale par markup hamesha bada number hota hai. Jo "
                 "trader markup mein sochta hai par distributor ko margin bata deta hai, woh "
                 "khud ko 20% kam price par pa sakta hai."),
        "formula": ("Markup % = (Selling Price − Cost Price) ÷ Cost Price × 100. Margin % = "
                    "(Selling Price − Cost Price) ÷ Selling Price × 100. ₹600 mein kharido, "
                    "₹1,000 mein becho: profit ₹400, jo 66.7% markup hai par sirf 40% margin. "
                    "Yahi gap hai isliye '40% margin' wala product '40% markup' wala nahi hota, "
                    "aur dono confuse karne se bade order par asli paisa jaata hai."),
        "when": ["Product ki pricing kar rahe ho aur profit dono tarah se sahi batana hai.",
                 "Buyer margin maang raha hai aur usse woh price nikaalni hai jo charge karni padegi.",
                 "Competitor ki pricing se compare kar rahe ho aur barabar ka number chahiye."],
        "mistakes": ["Buyer ko margin ki jagah markup bata dena, jisse aapki price zyada lagti hai.",
                     "Cost par margin jodkar selling price nikaalna, jabki margin selling price ka hissa hota hai.",
                     "Ye bhool jaana ki discount dene par dono numbers girti hain, kyunki selling price badal gaya."],
    },
    "breakeven": {
        "what": ("Break-even point woh exact sales volume hai jahan business paisa khona band "
                 "karta hai aur kamane lagta hai. Isse neeche har sale aapko fixed costs se "
                 "door rakhti hai; ispar rent, salary aur bills cover ho jaate hain; isse upar "
                 "har extra unit contribute karta hai. Yeh pehla number hai jo lender ya "
                 "investor actually maangta hai, kyunki ye batata hai ki business ki aaj ki "
                 "sales aur nuksan ke beech kitni jagah hai."),
        "formula": ("Break-Even Units = Fixed Costs ÷ (Selling Price − Variable Cost). "
                    "₹2,00,000 mahina fixed cost, ₹500 mein bikne wala product jiska variable "
                    "cost ₹300 hai, ₹200 contribution chhodta hai, toh break-even 1,000 units. "
                    "Rupees mein 1,000 × ₹500 = ₹5,00,000 mahina revenue. Price badhao ya "
                    "variable cost ghatao, break-even neeche aa jaata hai - yahi poora lever hai."),
        "when": ["Monthly sales target set kar rahe ho aur floor chahiye, aspiration nahi.",
                 "Dukaan ya hiring jaisi fixed costs lene ka faisla kar rahe ho.",
                 "Lender ya investor ne poocha hai ki khona band karne ke liye kitna bechna padega."],
        "mistakes": ["Kuch fixed costs chhod dena, jisse break-even asli se bahut kareeb lagta hai.",
                     "Gross revenue use karna contribution ki jagah - maayne rakhta hai har unit apni variable cost ke baad kitna chhodti hai.",
                     "Break-even ko profit target samajh lena. Break-even par kuch nahi kamate; wahan loss rukta hai."],
    },
    "ccc": {
        "what": ("Cash conversion cycle batata hai ki stock ke liye paisa dene se lekar "
                 "customers se paisa aane tak aapka paisa business mein kitne din phasa rehta "
                 "hai. Business kagaz par profitable ho sakta hai aur phir bhi cash khatam ho "
                 "sakta hai - aur aksar yahi wajah hoti hai. Aap inventory kharidte ho, rakhte "
                 "ho, credit par bechte ho, aur tab jaakar collect karte ho. Us chain ka har din "
                 "aapke paise ka din hai jo kisi aur ke liye kaam kar raha hai. Cycle ghataana "
                 "aksar sales badhane se tez hota hai."),
        "formula": ("CCC = Days Inventory + Days Receivables − Days Payables. Stock 60 din "
                    "padha, customers 45 din mein pay karte hain, aur aap suppliers ko 30 din "
                    "mein dete ho, toh cycle 60 + 45 − 30 = 75 din. Matlab 75 din ki cost kahin "
                    "se fund karni padegi - aksar apni jeb se ya loan se. Supplier terms 30 ki "
                    "jagah 45 kar do toh cycle 60 din ho jaata hai, bina ek rupee extra sales ke."),
        "when": ["Profitable ho par hamesha cash ki kami rahe, aur dekhna hai paisa kahaan phasa hai.",
                 "Supplier ya bade customer ke saath payment terms negotiate kar rahe ho.",
                 "Busy season se pehle kitna working capital chahiye ye plan kar rahe ho."],
        "mistakes": ["Cycle best customer par measure karna, average par nahi. Ek slow payer poora number kheench leta hai.",
                     "Ratio sudharne ke liye payables badhana bina ye dekhe ki suppliers phir price badha dete hain ya supply band kar dete hain.",
                     "Profit ko cash samajh lena. 90-din cycle wala profitable business bhi doob sakta hai."],
    },
    "depreciation": {
        "what": ("Straight-line depreciation asset ki cost ko un saalon mein barabar baant deta "
                 "hai jinme aap use karne wale ho. ₹10 lakh ki machine jo das saal chalegi, "
                 "business ko har saal ₹1 lakh ki padti hai, chahe us saal kuch kharch na kiya "
                 "ho. Yeh cash payment nahi hai - yeh accounting ka tareeka hai asset ki cost "
                 "ko un saalon se match karne ka jo usse faayda uthate hain, aur yahi profit "
                 "figure ko imaandar banata hai."),
        "formula": ("Yearly Depreciation = (Asset Cost − Salvage Value) ÷ Useful Life. "
                    "₹10,00,000 ki machine, ₹1,00,000 resale value, 10 saal: (10,00,000 − "
                    "1,00,000) ÷ 10 = ₹90,000 saalana. Chaar saal baad book value ₹10,00,000 − "
                    "₹3,60,000 = ₹6,40,000. Tax ke liye Income Tax Act written-down value "
                    "blocks use karta hai, isliye accounting figure aur tax figure alag hote "
                    "hain - accountant dono reconcile karta hai."),
        "when": ["Accounts taiyaar kar rahe ho aur asset ka saalana charge chahiye.",
                 "Equipment kharidna hai ya kiraye par lena hai - asli saalana cost maayne rakhti hai.",
                 "Jaanna hai ki asset books par abhi kitne ka hai."],
        "mistakes": ["Depreciation ko business se jaata cash samajh lena. Yeh non-cash charge hai aur paisa asset kharidte waqt gaya tha.",
                     "Useful life bahut lambi rakhna taaki profit achha dikhe - phir asset likhne se pehle toot jaata hai.",
                     "Ye bhool jaana ki tax depreciation Income Tax Act ke rates par chalti hai, aapke anumaan par nahi."],
    },
    "gst": {
        "what": ("GST calculator wahi do kaam karta hai jo aapko hamesha chahiye: price par GST "
                 "jodkar final bill nikalna, aur aisi amount se GST nikaalna jisme woh pehle se "
                 "shaamil hai. Doosri direction hi logon ko phasati hai, kyunki GST-inclusive "
                 "price ke andar base chhota hota hai jitna woh dikhta hai. India mein rate "
                 "state ke andar bikri par CGST aur SGST mein bat jaata hai, ya state ke bahar "
                 "bikri par ek IGST - par total wahi rehta hai."),
        "formula": ("GST Amount = Base Price × GST Rate ÷ 100, aur final price Base + GST hai. "
                    "₹1,000 base par 18% GST = ₹180 aur ₹1,180 ka bill. Ulta: agar bill 18% GST "
                    "ke saath ₹1,180 hai, toh base 1,180 ÷ 1.18 = ₹1,000 aur tax ₹180 hai. "
                    "Ulta direction division use karti hai, subtraction nahi - ₹1,180 se 18% "
                    "ghatao toh ₹967.60 aata hai, jo galat hai."),
        "when": ["Invoice bana rahe ho aur GST amount aur total chahiye.",
                 "Price inclusive batayi gayi hai aur base aur tax alag karne hain.",
                 "GST-inclusive price ko GST-exclusive se compare karna hai."],
        "mistakes": ["Inclusive price se GST rate ghata dena, (1 + rate) se divide karne ki jagah. Isse base hamesha kam aata hai.",
                     "Ye bhool jaana ki supply se pehle discount dene par GST discounted price par lagti hai, par baad mein dene par poori price par.",
                     "GST ko apna paisa samajh lena. Woh sarkar ke liye rakha jaata hai aur dena padta hai."],
    },
    "gst_taxwealth": {
        "what": ("Yeh GST calculator thoda messy asli case sambhalta hai: pehle discount lagta "
                 "hai, phir bache hue par GST lagti hai, aur tax aapke liye CGST aur SGST mein "
                 "bat jaati hai. Order maayne rakhta hai. 10% discount ke baad 18% GST ka jawab "
                 "gross par pehle 18% GST aur baad mein 10% discount se alag hota hai, aur "
                 "galat order ka matlab invoice aapki books se match nahi karega."),
        "formula": ("Discounted Base = Base Amount × (1 − Discount %). GST = Discounted Base × "
                    "GST Rate. Total = Discounted Base + GST, jisme intra-state sale par CGST "
                    "aur SGST dono rate ke aadhe-aadhe. ₹10,000 base, 10% discount aur 18% GST: "
                    "base ₹9,000 ho jaata hai, GST ₹1,620 jo ₹810 CGST aur ₹810 SGST mein bat "
                    "jaati hai, aur invoice total ₹10,620."),
        "when": ["Trade discount ke saath invoice issue kar rahe ho aur uspar GST.",
                 "Intra-state sale ke liye CGST aur SGST split chahiye.",
                 "GST-inclusive amount se base reverse nikaalna hai."],
        "mistakes": ["Pre-discount amount par GST lagana. Invoice par dikhaye gaye discount par GST discounted value par lagti hai.",
                     "Inter-state sale mein tax barabar baant dena - wahan poore rate par IGST hona chahiye, CGST plus SGST nahi.",
                     "CGST aur SGST alag-alag round karke total ko invoice se ek-do rupee hilne dena."],
    },
    "landed": {
        "what": ("Landed cost matlab product ko apne warehouse tak laane ki asli kul cost, aur "
                 "yeh lagbhag hamesha invoice se zyada hoti hai. Manufacturing pehli line hi "
                 "hai - packaging, freight, insurance, customs clearance aur godown tak ki "
                 "last-mile delivery sab usi unit par aate hain. Jo founder sirf manufacturing "
                 "cost se price karta hai, usse mahino baad pata chalta hai ki woh loss par "
                 "bech raha tha, kyunki jo number use kiya woh asli cost hi nahi thi."),
        "formula": ("Landed Cost per Unit = (Manufacturing + Packaging + Shipping + Other "
                    "Costs) ÷ Units. 1,000 units ka batch, banane mein ₹4,00,000, pack karne "
                    "mein ₹40,000, ship karne mein ₹60,000 aur baaki ₹30,000: (4,00,000 + "
                    "40,000 + 60,000 + 30,000) ÷ 1,000 = ₹530 per unit. Agar aap ₹500 par bech "
                    "rahe the, toh har sale par ₹30 ka loss tha - aur yahi nikaalna is "
                    "calculator ka poora point hai."),
        "when": ["Selling price set kar rahe ho aur ek unit ki asli cost chahiye.",
                 "Domestic supplier ko imported supplier se compare kar rahe ho.",
                 "Check karna hai ki koi product line actually paisa bana rahi hai ya nahi."],
        "mistakes": ["Manufacturing cost se price karna aur freight aur clearance chhod dena.",
                     "Tooling jaise one-off costs ko ek hi batch par baant dena, un volumes par nahi jinme woh kaam karenge.",
                     "Ye bhool jaana ki import par di gayi duties aur taxes baad mein credit ho sakti hain, isliye cash cost aur asli cost alag hote hain."],
    },
    "discountimpact": {
        "what": ("Discount impact calculator dikhata hai ki discount aapko actually kitna "
                 "padta hai, aur yeh percentage se kaafi zyada hota hai. 40% margin wale "
                 "product par 10% discount aapke profit ka 10% nahi khaata - chauthai kha "
                 "jaata hai. Yahi number founders miss karte hain jab woh deal close karne ke "
                 "liye 'chhota' discount dete hain, kyunki discount price se jaata hai par "
                 "cost bilkul wahin rehti hai."),
        "formula": ("New Price = Selling Price × (1 − Discount %). New Profit = New Price − "
                    "Cost Price. ₹1,000 mein bikne wala product jiski cost ₹600 hai, ₹400 "
                    "profit deta hai. 10% discount se price ₹900, toh profit ₹300 - 10% "
                    "discount par profit mein 25% ki giri. Khooye profit ko wapas kamane ke "
                    "liye 33% zyada volume chahiye, isliye blanket discounts itne kam kaam ke "
                    "hote hain."),
        "when": ["Customer discount maang raha hai aur asli cost jaanna hai.",
                 "Sale chala rahe ho aur break-even ke liye zaroori volume nikaalna hai.",
                 "Discount ko sale jeetne ke doosre tareekon se compare kar rahe ho."],
        "mistakes": ["Discount ko profit ke percentage ki tarah padhna. Yeh price se jaata hai, aur profit bahut chhota number hota hai.",
                     "Discount dene se pehle ye nikaalna nahi ki usse justify karne ke liye kitna extra volume chahiye.",
                     "Kam margin wale product par discount dena, jahan wahi percentage lagbhag poora profit kha jaata hai."],
    },
    "homeemi": {
        "what": ("Home loan EMI calculator housing loan ki fixed monthly payment dikhata hai, "
                 "aur usse zyada zaroori - loan aapko kul kitne ka padta hai. EMI ke do hisse "
                 "hote hain - byaaj aur principal - aur shuru ke saalon mein lagbhag poora "
                 "byaaj hi hota hai. Isliye 8.5% par 20 saal ka loan borrow ki gayi rakam se "
                 "kaafi zyada padta hai, aur isliye shuru ke saalon mein chhoti prepayment baad "
                 "mein utni hi rakam dene se kaafi zyada bachaati hai."),
        "formula": ("EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1), jahan P loan amount hai, r monthly "
                    "interest rate (saalana rate ÷ 12 ÷ 100) aur n mahine. ₹50 lakh loan 8.5% "
                    "par 20 saal: EMI takreeban ₹43,391, aur poori term mein kul takreeban "
                    "₹1.04 crore - lagbhag dugna. Wahi loan 30 saal par EMI takreeban ₹38,446 "
                    "kar deta hai par kul cost takreeban ₹1.38 crore."),
        "when": ["Do banks ke offers alag rates aur tenure par compare kar rahe ho.",
                 "Jaanna hai ki lambi tenure aapko kul byaaj mein kitna padti hai.",
                 "Faisla karna hai ki extra paisa prepay karna hai ya invest."],
        "mistakes": ["Sabse kam EMI ke liye sabse lambi tenure chunna. Monthly bachat chhoti hoti hai aur extra byaaj bada.",
                     "Ye ignore karna ki floating rate par EMI ya tenure badal sakti hai, aur total fix nahi hai.",
                     "Processing fees, insurance aur loan agreement ki stamp duty bhool jaana, jo EMI mein nahi aate."],
    },
    "landunits": {
        "what": ("Land area unit converter square feet ko un units mein badalta hai jinme India "
                 "mein zameen actually bikti hai - square yards, square metres, aur woh "
                 "traditional units jo bahut states mein property deals par raaj karte hain: "
                 "guntha, cent, bigha aur acre. Yeh maayne rakhta hai kyunki ek unit mein "
                 "bataya plot aur doosre unit se compare karna barabar ka comparison nahi hai, "
                 "aur traditional units state-dar-state badalte hain, toh ek state ka bigha "
                 "doosre state ka bigha nahi hai."),
        "formula": ("1 square yard = 9 square feet. 1 square metre = 10.764 square feet. 1 acre "
                    "= 43,560 square feet, matlab 4,840 square yards. 1 guntha = 1,089 square "
                    "feet, toh 40 guntha ka ek acre. 1 cent = 435.6 square feet, toh 100 cent ka "
                    "ek acre. 2,400 square feet ka plot 266.7 square yards ya takreeban 223 "
                    "square metres hai - kaam ka jab buyer aur seller ek hi zameen ke liye alag "
                    "units bol rahe hon."),
        "when": ["Plot ek unit mein bataya hai aur doosre se compare karna hai.",
                 "Sale deed ya 7/12 extract padh rahe ho aur area apni samajh ke unit mein chahiye.",
                 "Listing ke liye traditional units aur square feet ke beech convert karna hai."],
        "mistakes": ["Maanna ki bigha ya guntha poore India mein same hai. Ye units state aur kabhi district ke hisaab se badalte hain.",
                     "Square feet aur square yards mix kar dena, jinme nau guna ka farq hai.",
                     "Area convert karna par survey number aur boundaries deed se check na karna."],
    },
    "ctc": {
        "what": ("CTC calculator dikhata hai ki ek employee par company ka actually kitna kharch "
                 "hota hai, jo offer letter ki salary se hamesha zyada hota hai. Gross salary ke "
                 "upar employer provident fund deta hai, aur aksar gratuity, insurance aur "
                 "doosre benefits bhi. Chhote business owner ke liye yahi number budget karna "
                 "hai, kyunki ₹50,000 mahina par hiring ₹50,000 mahina se kaafi zyada padti "
                 "hai. Employee ke liye ye samjhata hai ki take-home CTC se kam kyun hota hai."),
        "formula": ("Employer Cost = Gross Monthly Salary + Employer PF + Other Monthly "
                    "Benefits, aur saalana figure uska barah guna. ₹50,000 gross salary, 12% "
                    "employer PF ₹6,000 aur ₹2,000 doosre benefits: mahina ₹58,000, saalana "
                    "₹6,96,000. Basic ka takreeban 4.81% gratuity jodo toh asli saalana cost "
                    "₹7 lakh cross kar jaati hai - jabki CTC ₹6 lakh lag rahi thi."),
        "when": ["Hiring kar rahe ho aur budget ke liye asli monthly cost chahiye.",
                 "Employee ho aur check karna hai ki take-home CTC se itna kam kyun hai.",
                 "Full-time hire ko freelancer se compare kar rahe ho."],
        "mistakes": ["Sirf gross salary budget karna aur PF aur benefits ki cost par chaunk jaana.",
                     "CTC ko take-home samajh lena. CTC mein employer contributions hote hain jo employee ke bank account tak nahi pahunchte.",
                     "Gratuity bhool jaana, jo har saal jama hoti hai aur service ke ant mein deni padti hai."],
    },
    "freelance": {
        "what": ("Freelancer hourly rate calculator nikalta hai ki target income tak pahunchne "
                 "ke liye aapko per hour kitna charge karna chahiye - aur jawab hamesha "
                 "freelancers ke pehle anumaan se zyada hota hai. Wajah ye hai ki freelancer ke "
                 "billable ghante kaam ke ghanton ka ek hissa hi hote hain. Sales, invoicing, "
                 "seekhna, admin aur projects ke beech ke gaps - sab asli waqt hai jiska koi "
                 "paisa nahi deta, aur 40-ghante ke week par set kiya rate aisa rate hai jo "
                 "aapko underpaid chhod dega."),
        "formula": ("Hourly Rate = Target Monthly Income ÷ Billable Hours per Month. ₹1,00,000 "
                    "mahina chahiye, 40 ghante hafta kaam par unme sirf 50% billable, aur 4 "
                    "hafte: 80 billable ghante. ₹1,00,000 ÷ 80 = ₹1,250 ghanta. ₹800 charge karo "
                    "toh ₹64,000 kamayenge, chahe kitni bhi mehnat karo. Billable percentage "
                    "wahi number hai jise freelancers lagataar zyada aankte hain."),
        "when": ["Client ko quote kar rahe ho aur aisa rate chahiye jo actually pay kare.",
                 "Job se freelancing par aa rahe ho aur purani salary match karni hai.",
                 "Faisla karna hai ki diye gaye price par project lena worth hai ya nahi."],
        "mistakes": ["Maanna ki har kaam ka ghanta billable hai. Zyadatar freelancers best case 50% se 70% hi bill karte hain.",
                     "Rate competitor ke price se set karna, apni zaroori income se nahi.",
                     "Tax bhool jaana, aur ye ki aap khud apna PF, insurance aur chhuttiyan dete ho."],
    },
    "franchise": {
        "what": ("Franchise ya store ROI calculator wahi ek sawaal ka jawab deta hai jo kholne "
                 "ka faisla karta hai: paisa wapas aane mein kitna waqt lagega? Store ki upfront "
                 "cost - franchise fee, deposit, fit-out, shuru ka stock - badi hoti hai aur "
                 "zyadatar sunk, aur monthly profit usi ko wapas karta hai. ₹25 lakh mein khulne "
                 "wala outlet jo ₹1.5 lakh mahina kamata hai, takreeban 17 mahine mein payback "
                 "karta hai, aur yahi number franchise agreement ki term se compare karna hai."),
        "formula": ("Payback Period mahino mein = Starting Investment ÷ Monthly Profit. ₹25 "
                    "lakh investment, ₹1,50,000 mahina profit: takreeban 17 mahine mein payback. "
                    "ROI matlab saalana profit divided by investment: ₹18,00,000 ÷ ₹25,00,000 = "
                    "72% saalana, jo shaandaar lagta hai jab tak check na karo ki ₹1.5 lakh "
                    "realistic mahina hai ya best mahina. Agreement ki term se aage payback "
                    "matlab model kaam nahi karta."),
        "when": ["Franchise offer evaluate kar rahe ho aur sign karne se pehle payback chahiye.",
                 "Do locations compare kar rahe ho jinke rent aur expected sales alag hain.",
                 "Doosra outlet kholna hai ya nahi ye decide kar rahe ho."],
        "mistakes": ["Franchisor ke projected sales use karna, apne conservative figure ki jagah.",
                     "Working capital investment se bahar chhod dena. Store ko stock aur cash chahiye isse pehle ki woh kamaye.",
                     "Royalty aur marketing fees ignore karna, jo monthly profit se pehle nikal jaati hain."],
    },
    "funnel": {
        "what": ("Marketing funnel calculator dikhata hai ki aap har step par kitna dete ho - per "
                 "click, per lead aur per sale - taaki saaf dikhe ki paisa kahaan leak ho raha "
                 "hai. Har stage ki apni cost hoti hai, aur har stage ki cost pichhli stage "
                 "divided by uske conversion rate hoti hai. Zyadatar businesses ad spend aur "
                 "sales jaante hain aur beech mein kuch nahi, jisse ye pata karna namumkin ho "
                 "jaata hai ki problem ad hai, landing page hai ya follow-up."),
        "formula": ("CPC = Ad Spend ÷ Clicks. CPL = Ad Spend ÷ Leads. CPA = Ad Spend ÷ "
                    "Conversions. ₹50,000 se 2,500 clicks, 250 leads aur 25 sales: CPC ₹20, CPL "
                    "₹200 aur CPA ₹2,000. Ab dikh jaata hai ki lead-to-sale rate 20% karne se "
                    "CPA ₹1,000 ho jaata hai - jo CPC aadha karne se kaafi sasta hai."),
        "when": ["Campaign profitable nahi hai aur dhoondhna hai kaunsa stage fail ho raha hai.",
                 "Launch se pehle CPC, CPL aur CPA ke targets set kar rahe ho.",
                 "Do channels compare kar rahe ho jo sirf ad spend par same lagte hain."],
        "mistakes": ["CPC sudharna jab leak funnel mein neeche hai. Jo sasta click kabhi convert nahi hota, bekaar hai.",
                     "Channel ko last click par measure karna jab customer ne pehle teen touchpoints dekhe the.",
                     "CPA channels ke beech compare karna bina ye dekhe ki har channel ka customer kaisa hai."],
    },
    "saas": {
        "what": ("ARPU, MRR aur ARR woh teen numbers hain jin par har subscription ya app "
                 "business judge hota hai. MRR woh recurring revenue hai jo aap har mahine expect "
                 "kar sakte ho, ARR wahi saalana bana hua, aur ARPU average revenue per user. "
                 "Investors inhe lagbhag sabse pehle dekhte hain, kyunki recurring revenue "
                 "one-off sales se kaafi zyada keemti hoti hai - isse forecast kiya ja sakta "
                 "hai, aur customers rukne se ye compound hoti hai."),
        "formula": ("MRR = subscriptions se total monthly revenue. ARR = MRR × 12. ARPU = MRR ÷ "
                    "Active Users. ₹8,00,000 monthly subscription revenue = ₹96,00,000 ARR. "
                    "2,000 active users ke saath ARPU ₹400 mahina. Do cheezein inhe hilati hain: "
                    "naye customers MRR badhate hain, aur churn isse ghatata hai. Jo business MRR "
                    "badha raha hai par har mahine 8% customers kho raha hai, woh chhedi hui "
                    "balti bhar raha hai."),
        "when": ["Paisa raise kar rahe ho aur MRR aur ARR sahi batana hai.",
                 "Do pricing plans compare kar rahe ho aur dekhna hai kaunsa ARPU badhata hai.",
                 "Track kar rahe ho ki growth asli hai ya sirf churn bhar rahi hai."],
        "mistakes": ["One-off setup fees ya annual prepayments ko MRR ginna. Isme sirf recurring revenue aati hai.",
                     "Ek achhe mahine se ARR batana, current run rate se nahi.",
                     "ARPU dekhna par churn nahi. Zyada ARPU aur zyada churn ke saath business phir bhi sikud jaata hai."],
    },
    "agencycac": {
        "what": ("Client acquisition cost matlab aapki agency ek client jeetne par kitna kharch "
                 "karti hai, aur yahi number tay karta hai ki marketing par kitna kharch kar "
                 "sakte ho. Yeh sirf ad spend nahi hai - isme salesperson ki cost, woh pitches "
                 "jo kahin nahi pahunchi, aur leads dhoondhne-follow karne ke tools bhi shaamil "
                 "hain. Jo agency ek quarter mein 10 clients jeetne ke liye ₹5 lakh kharch karti "
                 "hai, uska CAC ₹50,000 hai, aur agar woh clients apni life mein ₹2 lakh ke hain "
                 "toh maths chalta hai."),
        "formula": ("CAC = (Marketing Spend + Sales Cost) ÷ New Clients. ₹4,00,000 marketing "
                    "aur ₹1,00,000 sales cost se 10 clients: CAC ₹50,000. Client lifetime value "
                    "se compare karo: agar LTV ₹2,00,000 hai toh ratio 4:1, jo healthy hai. 3:1 "
                    "se neeche agency grow karne par zyada kharch kar rahi hai, aur har naya "
                    "client cash position ko pehle kharab karta hai."),
        "when": ["Marketing budget set kar rahe ho aur jaanna hai client kitne ka pad sakta hai.",
                 "Paid channels ko referrals aur outbound se compare kar rahe ho.",
                 "Check kar rahe ho ki growth actually profitable hai ya nahi."],
        "mistakes": ["Sirf ad spend ginna aur sales salary aur tools bahar chhod dena.",
                     "Sab leads par divide karna, actually jeete clients par nahi.",
                     "CAC ko ek mahine ki fee se compare karna, client ke poori life value se nahi."],
    },
    "agencymargin": {
        "what": ("Agency profit margin matlab delivery aur operating costs ke baad revenue ka "
                 "kitna bachta hai, aur agencies revenue ko profit samajhne ke liye mashhoor "
                 "hain. ₹1 crore ki agency jiska kharch ₹95 lakh hai, woh ₹5 lakh ka business "
                 "hai, ₹1 crore ka nahi. Do sabse bade leaks hain delivery cost - har client "
                 "jo team ka waqt khaata hai - aur woh overhead jo agency ke saath chup-chaap "
                 "badhta hai: zyada tools, badi office, zyada admin."),
        "formula": ("Profit Margin % = (Revenue − Total Costs) ÷ Revenue × 100. ₹1,00,00,000 "
                    "revenue, ₹95,00,000 costs: ₹5,00,000 bachta hai, 5% margin. Services agency "
                    "ke liye 20% se 30% healthy hai aur 40% excellent. Sabse tez fix aksar price "
                    "hota hai, cost nahi: same cost base par 10% price badhane se 5% margin 14.5% "
                    "ho jaata hai, jitna tool-cutting se kabhi nahi hoga."),
        "when": ["Saal review kar rahe ho aur jaanna hai agency ne actually kitna kamaya.",
                 "Agle saal ki pricing set kar rahe ho aur zaroori margin chahiye.",
                 "Ek mahine ko pichhle saal ke same mahine se compare kar rahe ho."],
        "mistakes": ["Revenue ko profit kehna. Agency mein dono bahut alag hote hain.",
                     "Owner ki apni salary cost base se bahar chhod dena, jisse margin achha dikhta hai.",
                     "Tools aur software kaatna jab asli problem ye hai ki kaam ka price kam hai."],
    },
    "churn": {
        "what": ("Churn rate matlab ek period mein kitne percent clients ya customers jaate "
                 "hain, aur yahi number chup-chaap tay karta hai ki business badhega ya wahin "
                 "khada rahega. Har mahine 5% clients khona serious nahi lagta jab tak ye "
                 "samajh na aaye ki saal mein lagbhag aadhe chale jaate hain. Churn growth par "
                 "cap bhi lagata hai: agar har mahine 8 clients jaate hain aur 8 aate hain, toh "
                 "aap wahin rehne ke liye mehnat kar rahe ho."),
        "formula": ("Churn Rate % = Clients Lost ÷ Clients at Start × 100. 120 mein se 6 "
                    "clients khona = 5% monthly churn. Saalana, takreeban 46% base saal mein "
                    "chala jaata hai. Har mahine 10 clients badhne ke liye 16 jeetne padenge, "
                    "kyunki 6 jaa rahe hain. Churn 5% se 3% karna aksar naye sales dugna karne "
                    "se zyada kaam ka hota hai, aur sasta bhi, kyunki clients pehle se aapke "
                    "hain."),
        "when": ["Client retention review kar rahe ho aur imaandar monthly figure chahiye.",
                 "Sales target set kar rahe ho aur jaanna hai churn usme se kitna khaayega.",
                 "Faisla karna hai ki retention mein invest karna hai ya acquisition mein."],
        "mistakes": ["Churn saalana measure karna aur ye miss karna ki monthly figure compound hota hai.",
                     "Client ko retained ginna sirf isliye ki contract hai, chahe usne service use karna band kar diya ho.",
                     "Revenue churn batana jab sawaal customer churn ka tha - ek bada client jaane se dono bahut alag hilti hain."],
    },
    "breakevenad": {
        "what": ("Break-even ad spend matlab woh sabse zyada jo aap advertising par de sakte ho "
                 "isse pehle ki campaign paisa kamana band kar de. Yeh ceiling hai, target nahi, "
                 "aur ye aapke apne margin se set hoti hai - competitor kya bid kar rahe hain ya "
                 "platform kya suggest karta hai, usse nahi. ₹300 contribution wala product "
                 "sale jeetne ke liye usme se lagbhag poora kharch kar sakta hai aur phir bhi "
                 "break even, par usse upar har rupee loss hai. Yeh number jaanna aapko bid "
                 "karke loss mein jaane se rokta hai."),
        "formula": ("Contribution per Sale = Revenue per Sale − Product Cost per Sale. "
                    "Break-Even Ad Spend = Contribution per Sale × Expected Conversions. ₹1,000 "
                    "mein becho, product cost ₹600, contribution ₹400. 20 conversions expect "
                    "karte ho toh ₹8,000 tak kharch karke break even - ₹8,000 ad budget, ya "
                    "maximum ₹400 cost per acquisition. ₹10,000 kharch karo toh campaign ₹2,000 "
                    "khota hai."),
        "when": ["Maximum bid ya daily ad budget set kar rahe ho.",
                 "Campaign chal rahi hai aur jaanna hai kab band karni hai.",
                 "Do products compare kar rahe ho aur dekhna hai kaunsa zyada ad spend jhel sakta hai."],
        "mistakes": ["Contribution ki jagah revenue use karna. Ad spend afford karne se pehle product cost nikalni padti hai.",
                     "Break-even ko target samajh lena. Break-even par kuch nahi kamate; usse neeche kharch karna hai.",
                     "Delivery, packaging aur payment fees bhool jaana, jo contribution ghatate hain aur ceiling bhi."],
    },
    "pitchscore": {
        "what": ("Shark Tank pitch check aapke numbers ko un sawaalon par chalata hai jo sharks "
                 "actually poochte hain, aur batata hai kaunse sawaalon par aapko grilling "
                 "milegi. Shark Tank India par jaanch-paraakh kaafi consistent hai: aapki "
                 "valuation kya hai aur kyun, revenue aur margins kya hain, customer paane mein "
                 "kitna lagta hai, aur kitne mahine ka cash bacha hai? Jis pitch ke paas in "
                 "chaaron ke saaf jawab hain, woh room mein tik jaati hai."),
        "formula": ("Koi ek formula nahi hai - check ratios dekhta hai. Valuation vs revenue "
                    "batata hai ask kitna mehnga hai. LTV vs CAC batata hai growth profitable "
                    "hai ya nahi; 3:1 se neeche sharks push back karte hain. Runway mahino mein "
                    "batata hai business ke paas kitna waqt hai. Gross margin batata hai ki "
                    "product apni growth fund kar sakta hai ya nahi. ₹1 crore revenue par ₹10 "
                    "crore valuation 10x multiple hai, aur pitch ko woh justify karna padta hai."),
        "when": ["Pitch taiyaar kar rahe ho aur pehle apne kamzor numbers jaanna chahte ho.",
                 "Investor ne metrics maange hain aur unhe sanity-check karna hai.",
                 "Raise karne se pehle kya theek karna hai ye decide kar rahe ho."],
        "mistakes": ["Valuation lekar aana jise support karne ke liye revenue nahi hai. Multiple sabse pehle poochha jaata hai.",
                     "CAC aur LTV pata na hona jab poocha jaaye, jisse lagta hai apna business nahi jaante.",
                     "Aisa burn rate batana jisse runway chhota nikle aur uske liye plan na ho."],
    },
    "lovefun": {
        "what": ("Love calculator ek mazaak hai - do naam lete hain, unhe letter-based formula "
                 "se chalata hai, aur compatibility percentage deta hai. Yeh psychology, "
                 "astrology ya koi bhi claim wali cheez nahi hai, aur ise rishte ke baare mein "
                 "salah nahi samajhna chahiye. Yeh sirf isliye hai kyunki logon ko maza aata "
                 "hai, aur calculator site par kuch aise tools hone chahiye jo sirf "
                 "entertainment hain. Tank Metrics ise jaan-boojh kar entertainment likhta hai."),
        "formula": ("Score isse aata hai ki do naamon ke letters 'loves' phrase mein kitni baar "
                    "aate hain, totals ko weight diya jaata hai, aur result percentage mein "
                    "ghata diya jaata hai. Isme koi science nahi hai - wahi do naam hamesha wahi "
                    "number dete hain, aur yahi iski ekmaatra consistency hai. Output ko party "
                    "trick samjho, prediction nahi."),
        "when": ["Group chat ke liye halka-phulka jawab chahiye.",
                 "Jaanna hai ki wahi do naam dobara kitna score karte hain.",
                 "Kuch quick aur harmless share karna hai."],
        "mistakes": ["Result ko seriously lena. Yeh entertainment hai aur bas wahi.",
                     "Kam score se kuch matlab nikaalna. Iska koi aadhaar nahi hai.",
                     "Iska use asli rishte ke baare mein koi faisla karne ke liye karna."],
    },
    "babyname": {
        "what": ("Baby name number calculator naam ke letters ko numerology ke letter-values "
                 "se ek number mein badalta hai, aur dikhata hai ki woh number parampara mein "
                 "kisse juda hai. Bahut Indian families naam chunte waqt ise dekhti hain, rashi "
                 "aur nakshatra ke saath. Yeh parampara hai, science nahi, aur Tank Metrics ise "
                 "wahi kehta hai - kai inputs mein se ek, rule nahi."),
        "formula": ("Har letter ko Chaldean ya Pythagorean system mein 1 se 9 ka value milta "
                    "hai, values jodi jaati hain, aur digits ghataakar 1 se 9 ka single digit "
                    "banaya jaata hai - jab tak total 11, 22 ya 33 na ho, jinhe waise hi rakha "
                    "jaata hai. 'Aarav' 1 + 1 + 2 + 1 + 6 = 11 banta hai, jo master number hai "
                    "aur aage nahi ghatta."),
        "when": ["Do naam spellings ke beech choose kar rahe ho aur unke numbers compare karne hain.",
                 "Jaanna hai ki koi naam kis number par aata hai.",
                 "Rashi aur nakshatra ke saath ek paramparik input chahiye."],
        "mistakes": ["Number ko naam chunne ka sakht rule maan lena. Yeh parampara hai, requirement nahi.",
                     "Naam ki spelling badalne se alag jawab aata hai, aur ye na samajhna ki spelling ne number badla.",
                     "Sirf number ki wajah se rashi aur parivaar ki apni pasand ignore kar dena."],
    },
    "compatibility": {
        "what": ("Compatibility calculator do naamon ko ek playful scoring formula se compare "
                 "karta hai aur percentage deta hai. Yeh love calculator jaisa hi idea hai, "
                 "bas method alag - letters match hote hain, gine jaate hain aur ek score mein "
                 "ghata diye jaate hain. Iske peeche koi claim nahi hai aur koi evidence nahi "
                 "hai. Yeh fun tool hai, aur site ise insight batane ki jagah saaf-saaf yahi "
                 "kehti hai."),
        "formula": ("Dono naam letter-dar-letter match hote hain, common letters gine aur weight "
                    "kiye jaate hain, aur total 100 mein se percentage bana diya jaata hai. Wahi "
                    "jodi hamesha wahi result deti hai, aur yahi iski ekmaatra predictable baat "
                    "hai. Zyada score kam score se zyada matlab nahi rakhta - dono letters par "
                    "arithmetic hain."),
        "when": ["Quick, playful jawab share karna hai.",
                 "Jaanna hai do naam ek doosre ke against kitna score karte hain.",
                 "Assessment nahi, halka-phulka tool chahiye."],
        "mistakes": ["Score ko logon ke beech asli compatibility ka measure padhna.",
                     "Isse rishte ke baare mein koi nateeja nikaalna.",
                     "Ye maanna ki alag spelling se jawab nahi badlega - badlega."],
    },
    "daysbetween": {
        "what": ("Days between two dates do dates ke beech calendar din ginta hai, jo trivial "
                 "lagta hai jab tak iski zaroorat na pade. Iska use notice period, invoice due "
                 "dates, interest accrual, project timelines aur deadline se pehle bache din "
                 "nikaalne mein hota hai. Yeh calendar din ginta hai, working days nahi, isliye "
                 "30-din ka notice period weekends aur holidays bhi cover karta hai - aur isliye "
                 "'ek mahine' ka notice aksar 30 din se zyada hota hai."),
        "formula": ("Days = End Date − Start Date, calendar din mein. 1 April se 30 April 29 "
                    "din hai, 30 nahi, kyunki start date nahi ginti. 15 January se 15 March, "
                    "non-leap saal mein, 59 din hai. Due date ke liye invoice date par credit "
                    "period jodo: 1 March ke invoice par 45-din term 15 April ko due hota hai."),
        "when": ["Notice period ya contract deadline check kar rahe ho.",
                 "Nikaal rahe ho ki invoice actually kab due hota hai.",
                 "Project timeline plan kar rahe ho aur dinon ki ginti chahiye."],
        "mistakes": ["Start date ko din ek ginna, jisse har jawab mein ek din badh jaata hai.",
                     "Calendar din aur working days confuse karna. Sirf pehla weekends aur holidays ginnta hai.",
                     "Ye bhool jaana ki February leap year mein badalta hai, jisse uske baad ki har date khisak jaati hai."],
    },
    "bmi": {
        "what": ("BMI calculator height aur weight se body mass index estimate karta hai, jo "
                 "rough idea deta hai ki adult underweight, normal range, overweight ya obese "
                 "hai. Yeh screening tool hai, diagnosis nahi: ye muscle aur fat mein farq nahi "
                 "karta, aur bachchon, pregnant mahilaon ya bahut muscular logon ke liye banaya "
                 "hi nahi gaya. India mein healthy range neeche hai, kyunki diabetes aur heart "
                 "disease ka risk yahan Western populations se kam BMI par badhta hai."),
        "formula": ("BMI = Weight kilogram mein ÷ (Height metres mein)². 70 kg aur 1.70 m: 70 ÷ "
                    "(1.70 × 1.70) = 70 ÷ 2.89 = 24.2. WHO ranges: 18.5 se kam underweight, "
                    "18.5 se 24.9 normal, 25 se 29.9 overweight aur 30 se upar obese. Indians ke "
                    "liye health authorities aksar 23 ko normal ki upper limit maante hain, "
                    "isliye 24.2 BMI saavdhani hai, saaf bill of health nahi."),
        "when": ["Quick general idea chahiye ki aapka weight aapki height ke liye kahaan hai.",
                 "Ek number ki jagah waqt ke saath badlav track kar rahe ho.",
                 "Indian-adjusted range jaanna hai, jo WHO se neeche hai."],
        "mistakes": ["BMI ko diagnosis maan lena. Yeh screening estimate hai aur muscle, bone density aur body composition miss karta hai.",
                     "Indian adult ke liye WHO range use karna, jahan healthy ceiling neeche hai.",
                     "Ise bachchon ya pregnant mahilaon par lagana, jinke liye BMI sahi measure hi nahi hai."],
    },
})


# Two pages had an English guide but no Hinglish one; fill the gap so the
# translate button works on every tool.
HI_CALCS.update({
    "numwords": {
        "what": ("Number to words number ko Indian tareeke se shabdon mein likhta hai - lakh "
                 "aur crore, million aur billion nahi. Yeh cheque, invoice, legal document, "
                 "rent agreement aur har aise form ke liye bana hai jisme amount shabdon mein "
                 "maangta hai. Cheque par amount shabdon mein likhna isliye zaroori hai ki agar "
                 "figure mein koi badlav ho toh shabd wala version maanya hota hai, aur banks "
                 "isi ko dekhte hain. Indian numbering system har teen digit par comma lagata "
                 "hai, isliye yahan million-billion wala conversion seedha kaam nahi karta."),
        "formula": ("Indian grouping right se teen digit ke blocks mein hoti hai - pehle hazaar, "
                    "phir lakh, phir crore. 12,34,567 padha jaata hai 'twelve lakh thirty four "
                    "thousand five hundred sixty seven'. ₹10,00,000 'ten lakh' hai aur "
                    "₹1,00,00,000 'one crore'. Ulta conversion - crore ko million mein badalna - "
                    "ke liye 1 crore = 10 million aur 1 lakh = 100,000 yaad rakho."),
        "when": ["Cheque ya demand draft par amount shabdon mein likhni hai.",
                 "Legal document ya rent agreement mein figure shabdon mein chahiye.",
                 "Kisi foreign document ke liye crore aur lakh ko million mein badalna hai."],
        "mistakes": ["Million aur billion wala conversion Indian form par lagana, jahan lakh aur crore chahiye.",
                     "Comma galat jagah lagana. Indian system 12,34,567 likhta hai, 1,234,567 nahi.",
                     "Cheque par figure aur shabd match na hona - aisi cheque bank reject kar sakta hai."],
    },
    "marketshare": {
        "what": ("Market share calculator ek saada sawaal ka jawab deta hai: aapke market mein jo "
                 "kuch bika, usme se kitna aapka hai? Market mein bike total units aur aapke "
                 "bike units daalo, bas. Market share maayne rakhta hai kyunki yeh aapki growth "
                 "ko market ki growth ke saath tolta hai - agar aap 20% badhe par market 40% "
                 "badha, toh aapka share gir gaya, chahe revenue badhi ho. Investors ise dekhkar "
                 "batate hain ki aap jeet rahe ho ya sirf tez bah rahe ho."),
        "formula": ("Market Share % = (Your Units Sold ÷ Total Market Units) × 100. Aapne "
                    "12,000 units beche aur market mein 1,00,000 bike, toh share 12% hai. Value "
                    "share ke liye wahi formula revenue par lagao. 12% se 15% jaana 3 percentage "
                    "point ka gain hai par 25% ka rise - aur yeh farq batana zaroori hai kyunki "
                    "dono sahi lagte hain."),
        "when": ["Investor ko batana hai ki aap market mein kahaan khade ho.",
                 "Apni growth ko market ki growth se compare karna hai.",
                 "Kisi naye segment mein enter karne se pehle size dekhni hai."],
        "mistakes": ["Apna share apne pichhle saal se compare karna aur market ki growth bhool jaana.",
                     "Market ko bahut chhota ya bahut bada define karna, jisse share bekaar ho jaata hai.",
                     "Volume share aur value share mix kar dena - premium brand ka value share zyada hota hai."],
    },
})


def merge(path: Path, new: dict[str, dict]) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    before = len(data["calcs"])
    data["calcs"].update(new)
    # Keep the file diff-friendly: sort the hand-written entries by id.
    data["calcs"] = dict(sorted(data["calcs"].items()))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    return len(data["calcs"]) - before


def main() -> None:
    added_en = merge(EN, EN_CALCS)
    added_hi = merge(HI, HI_CALCS)
    print(f"tool_guides.json: +{added_en} hand-written guides")
    print(f"tool_guides_hinglish.json: +{added_hi} hand-written guides")
    # A dollar sign is the one thing Sir ruled out; catch it before it ships.
    for path in (EN, HI):
        text = path.read_text(encoding="utf-8")
        if "$" in text:
            raise SystemExit(f"{path.name} contains a dollar sign")


if __name__ == "__main__":
    main()
