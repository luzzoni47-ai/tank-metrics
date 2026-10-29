#!/usr/bin/env python3
"""De-dup batch 3: unique EN + Hinglish guides for 8 of the most duplicated pages.

tools/content_uniqueness.json shows 66 of 101 tool pages share a near-duplicate,
with a median 65% word overlap - they are all rendered from the same category
template. That is why Search Console reports 22 of them as "Discovered -
currently not indexed": Google has the URL, and no reason to fetch a near-copy.

The 8 chosen here are the worst overlaps that had no hand-written guide:
nps, sip, takehome, simpleint, fd, rd, wc, momyoy.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

EN = {
    "nps": {
        "what": "NPS, the National Pension Scheme, is a retirement account the government runs through PFRDA. You put money in every year, it gets invested in equity and debt funds you choose, and you cannot touch it until 60. The return is not fixed - it depends on the funds. What the calculator does is project the corpus at 60 from your monthly contribution, your current age and an assumed return, so you can see whether the number you are saving today actually reaches the retirement you want.",
        "formula": "Corpus = Monthly Contribution x [((1 + r)^n - 1) / r] x (1 + r), where r is the monthly rate (annual / 12) and n is months to 60. On top of this, the employer's 14% of basic (under Section 80CCD(2)) and the extra 50,000 rupee deduction under 80CCD(1B) are added.",
        "when": ["You are salaried and want to know how much the extra 50,000 rupee NPS deduction under 80CCD(1B) is actually worth.",
                 "You are choosing between NPS and PPF and want the projected corpus side by side.",
                 "You want to see what happens if you start 10 years later - the answer is usually brutal."],
        "mistakes": ["Assuming the calculator's return is guaranteed. NPS equity funds swing; a 10% assumption is a planning number, not a promise.",
                     "Forgetting that 40% of the corpus must buy an annuity at 60. The lump sum you can withdraw is smaller than the corpus shown.",
                     "Comparing NPS with an ELSS fund on tax alone. NPS locks the money to 60; ELSS unlocks in three years."],
    },
    "sip": {
        "what": "A SIP is a fixed amount invested in a mutual fund every month. The point of the calculator is compounding: 10,000 rupees a month for 20 years at 12% is not 24 lakh of contributions, it is about 99 lakh, and almost three quarters of that is growth you never deposited. The calculator separates your contribution from the growth, which is the number that makes people start a SIP rather than think about it.",
        "formula": "Future Value = P x [((1 + i)^n - 1) / i] x (1 + i), where P is the monthly amount, i is the monthly rate (annual / 12 / 100) and n is the number of instalments. Contribution = P x n; Growth = Future Value - Contribution.",
        "when": ["You are deciding whether to increase a SIP by 5,000 rupees a month and want to see the 20-year difference.",
                 "You want to know how many years a goal needs, given what you can afford monthly.",
                 "You are choosing between a 10% and a 12% fund and want to see whether the gap is worth the risk."],
        "mistakes": ["Using the fund's last-year return as the assumption. SIPs are planned on a long-run average, not last year's best.",
                     "Stopping the SIP in a falling market, which is exactly when you buy the most units per rupee.",
                     "Ignoring the expense ratio. A 1% higher ratio costs roughly a tenth of a 20-year corpus."],
    },
    "takehome": {
        "what": "Take-home is what lands in your bank after the employer deducts TDS, the employee's PF share, and professional tax. The gap between CTC and take-home is bigger than most people expect - on a 12 lakh CTC, the monthly credit is often closer to 80,000 rupees than 1,00,000, because the employer's PF and gratuity provisions are inside the CTC number but never reach you. The calculator does that subtraction line by line so the offer letter is readable.",
        "formula": "Take-home = Gross Salary - Employee PF (12% of basic) - Professional Tax - TDS. Gross = CTC - Employer PF - Gratuity - other retirals. TDS is then computed on the taxable gross after the standard deduction of 75,000 rupees.",
        "when": ["You have an offer letter in front of you and want to compare two CTCs on what you actually get monthly.",
                 "You are negotiating and need to know what a 1 lakh CTC increase is worth in hand.",
                 "You want to check whether the old or the new tax regime leaves you more this year."],
        "mistakes": ["Comparing a CTC that includes a big variable bonus against one that does not. The bonus is not monthly cash.",
                     "Forgetting that employer PF sits inside CTC. It is your money, but it is not in your account this month.",
                     "Assuming the TDS the employer deducts is the final tax. It is an estimate, and the March true-up is real."],
    },
    "simpleint": {
        "what": "Simple interest is charged only on the original amount, never on the interest already earned. 1,00,000 rupees at 10% for 3 years earns 30,000 - flat, every year, on the same 1,00,000. Compound interest on the same terms earns 33,100. The 3,100 rupee gap is small over three years and enormous over thirty, which is why knowing which one applies matters more than the rate itself.",
        "formula": "Interest = Principal x Rate x Time / 100. Total = Principal + Interest. For a part-year, Time is months / 12.",
        "when": ["A lender quotes a flat rate and you want the simple-interest figure to compare against a reducing-balance loan.",
                 "You are lending to a friend or relative and want a clear number in rupees.",
                 "You are checking a fixed-deposit or a bond coupon that pays simple interest."],
        "mistakes": ["Treating a flat rate as the real cost of a loan. A flat 10% on a reducing balance is closer to 18%.",
                     "Mixing up simple and compound when the period is long. Over 10 years the difference is not small.",
                     "Forgetting TDS on interest above the threshold, which reduces what you actually receive."],
    },
    "fd": {
        "what": "A fixed deposit pays a fixed rate for a fixed term, and the only decision that really changes the outcome is whether the interest is reinvested. 1,00,000 rupees at 7% for 5 years pays 35,000 in simple terms, but 40,255 if the interest compounds quarterly - and banks compound quarterly by default. The calculator shows both, plus the post-tax figure, because TDS on interest above 40,000 a year is what turns a 7% FD into about 4.9% for a taxpayer in the 30% slab.",
        "formula": "Maturity = P x (1 + r / n)^(n x t), where r is the annual rate, n the compounds per year (4 for quarterly) and t the years. Interest = Maturity - P.",
        "when": ["You are parking a lump sum and want the post-tax maturity, not the advertised rate.",
                 "You are comparing a bank FD with a small-finance bank FD that pays 0.5-1% more.",
                 "You are deciding between a 3-year and a 5-year FD and want the rupee difference."],
        "mistakes": ["Comparing an FD rate against an equity fund's return. The FD is contractual; the fund is not.",
                     "Ignoring TDS. For anyone in the 30% slab, an FD's real return is roughly the rate minus 30%.",
                     "Breaking an FD early without checking the penalty - typically 0.5-1% of the rate."],
    },
    "rd": {
        "what": "A recurring deposit is a monthly commitment to the same rate, with the bank paying interest on each instalment from the day it lands. 5,000 rupees a month for 5 years at 7% grows to about 3.6 lakh, of which 3 lakh is your own money. It is the deposit equivalent of a SIP, and the calculator's job is to show the interest separately from the contributions so the return is honest.",
        "formula": "Maturity = sum of P x (1 + r / 4)^(quarters remaining), over each monthly instalment. Interest = Maturity - (P x months).",
        "when": ["You want a fixed-return monthly habit and want to know the maturity before committing.",
                 "You are comparing an RD with a debt mutual fund for a 3-year goal.",
                 "You want to see what the last instalment earns versus the first - the difference surprises people."],
        "mistakes": ["Expecting the advertised rate to apply to the whole balance. Each instalment earns only for the time it is in.",
                     "Missing an instalment and assuming no penalty. Banks charge it, and it can reset the rate.",
                     "Using an RD for a 10-year goal. Compounding equity usually wins over that horizon."],
    },
    "wc": {
        "what": "Working capital is the money tied up in running the business day to day: stock on the shelf, plus what customers owe you, minus what you owe suppliers. A business can be profitable and still run out of cash, because profit is an accounting number and working capital is cash. The calculator turns the three lines into one figure and a cycle length, so you can see how many days your money is locked up before it comes back.",
        "formula": "Working Capital = Current Assets - Current Liabilities. Cash Conversion Cycle = Days Inventory + Days Receivable - Days Payable.",
        "when": ["You are profitable but the bank account keeps going to zero and you need to see where the money sits.",
                 "A customer asks for 60-day terms and you want to price what that costs you.",
                 "You are applying for a working-capital limit and need the number a bank will ask for."],
        "mistakes": ["Counting only stock and forgetting receivables. Slow-paying customers tie up more cash than slow-moving stock.",
                     "Treating a negative working capital as always bad. For a subscription business with prepaid plans it is healthy.",
                     "Ignoring the cycle length. 50 lakh tied up for 90 days is a very different business from the same amount tied up for 15."],
    },
    "momyoy": {
        "what": "Month-on-month compares this month with last month. Year-on-year compares this month with the same month a year ago. For almost every Indian business the YoY number is the honest one, because Diwali, the monsoon and the school calendar move demand so much that a MoM comparison mostly measures the festival, not the business. The calculator gives both, and the gap between them is the seasonality.",
        "formula": "MoM % = (This Month - Last Month) / Last Month x 100. YoY % = (This Month - Same Month Last Year) / Same Month Last Year x 100.",
        "when": ["A month looks bad and you want to know whether it is seasonality or a real decline.",
                 "You are presenting to an investor and need to show growth without the festive distortion.",
                 "You are setting next quarter's target and want a seasonal baseline to build on."],
        "mistakes": ["Reporting MoM growth in a festive month as if it were a trend. October always beats September.",
                     "Comparing a 31-day month with a 28-day month without normalising for days.",
                     "Using YoY on a business that is less than a year old - there is nothing to compare against yet."],
    },
}

HI = {
    "nps": {
        "what": "NPS yaani National Pension Scheme, sarkar ka PFRDA ke through chalaya gaya retirement account hai. Aap har saal paisa daalte ho, wo aapke chune equity aur debt funds me invest hota hai, aur 60 saal se pehle nikal nahi sakte. Return fixed nahi hai - funds par depend karta hai. Calculator aapki monthly contribution, umar aur maan liye gaye return se 60 par corpus project karta hai, taaki pata chale ki aaj ki saving se wahi retirement milega ya nahi.",
        "formula": "Corpus = Monthly Contribution x [((1 + r)^n - 1) / r] x (1 + r), jahan r monthly rate (annual / 12) aur n 60 tak ke mahine. Iske upar employer ka basic ka 14% (Section 80CCD(2)) aur 80CCD(1B) ke tahat extra 50,000 rupaye ki deduction judti hai.",
        "when": ["Aap salaried ho aur jaanna chahte ho ki 80CCD(1B) ki extra 50,000 rupaye deduction ki asli value kitni hai.",
                 "NPS aur PPF me choose kar rahe ho aur dono ka corpus saath dekhna chahte ho.",
                 "Aap dekhna chahte ho ki 10 saal late start karne par kya hota hai - jawab usually brutal hota hai."],
        "mistakes": ["Calculator ka return guaranteed maan lena. NPS equity funds upar-neeche hote hain; 10% planning number hai, promise nahi.",
                     "Ye bhoolna ki 60 par corpus ka 40% annuity kharidna padta hai. Withdraw karne wala lump sum dikhaye corpus se kam hai.",
                     "NPS ko sirf tax par ELSS se compare karna. NPS paisa 60 tak lock karta hai; ELSS 3 saal me khulta hai."],
    },
    "sip": {
        "what": "SIP matlab har mahine ek fixed amount mutual fund me daalna. Calculator ka poora point compounding hai: 10,000 rupaye mahina 20 saal 12% par 24 lakh ka contribution nahi, lagbhag 99 lakh banta hai, aur usme se teen-chauthai wo growth hai jo aapne kabhi jama hi nahi ki. Calculator aapka paisa aur growth alag dikhata hai, aur yahi number logon ko SIP shuru karwata hai.",
        "formula": "Future Value = P x [((1 + i)^n - 1) / i] x (1 + i), jahan P monthly amount, i monthly rate (annual / 12 / 100) aur n instalments. Contribution = P x n; Growth = Future Value - Contribution.",
        "when": ["Aap SIP 5,000 rupaye badhane ka soch rahe ho aur 20 saal ka farak dekhna chahte ho.",
                 "Aapko jaanna hai ki jo afford kar sakte ho usse goal kitne saal me pura hoga.",
                 "10% aur 12% fund me choose kar rahe ho aur dekhna chahte ho ki risk ke layak gap hai ya nahi."],
        "mistakes": ["Fund ke pichhle saal ke return ko assumption bana lena. SIP long-run average par plan hoti hai, pichhle saal ke best par nahi.",
                     "Girte market me SIP band kar dena - aur yahi waqt hai jab har rupee par sabse zyada units milte hain.",
                     "Expense ratio ignore karna. 1% zyada ratio 20 saal ke corpus ka lagbhag dasva hissa kha jata hai."],
    },
    "takehome": {
        "what": "Take-home wo hai jo employer TDS, employee ka PF share aur professional tax kaatne ke baad bank me aata hai. CTC aur take-home ka gap zyada logon ki expectation se bada hota hai - 12 lakh CTC par monthly credit aksar 1,00,000 se zyada 80,000 ke aas-paas hota hai, kyunki employer ka PF aur gratuity CTC number ke andar hote hain par aapke haath me nahi aate. Calculator ye ghatav line by line karta hai.",
        "formula": "Take-home = Gross Salary - Employee PF (basic ka 12%) - Professional Tax - TDS. Gross = CTC - Employer PF - Gratuity - doosre retirals. Phir 75,000 rupaye standard deduction ke baad taxable gross par TDS nikalta hai.",
        "when": ["Offer letter saamne hai aur do CTC ko monthly in-hand par compare karna hai.",
                 "Negotiation chal rahi hai aur 1 lakh CTC badhne par haath me kitna aayega ye jaanna hai.",
                 "Aap check karna chahte ho ki is saal purana ya naya tax regime zyada deta hai."],
        "mistakes": ["Bade variable bonus wali CTC ko bina bonus wali se compare karna. Bonus monthly cash nahi hai.",
                     "Ye bhoolna ki employer PF CTC ke andar hai. Wo aapka paisa hai, par is mahine account me nahi.",
                     "Employer ka deducted TDS ko final tax maan lena. Wo estimate hai, aur March ka true-up asli hota hai."],
    },
    "simpleint": {
        "what": "Simple interest sirf mool amount par lagta hai, kamaye gaye interest par kabhi nahi. 1,00,000 rupaye 10% par 3 saal me 30,000 kamata hai - flat, har saal, usi 1,00,000 par. Usi terms par compound interest 33,100 kamata hai. Teen saal me 3,100 ka farak chhota hai aur tees saal me bahut bada, isliye kaun sa lagta hai ye jaanna rate se zyada zaroori hai.",
        "formula": "Interest = Principal x Rate x Time / 100. Total = Principal + Interest. Saal se kam ke liye Time = mahine / 12.",
        "when": ["Koi lender flat rate bolta hai aur aapko reducing-balance loan se compare karne ke liye simple-interest number chahiye.",
                 "Aap kisi dost ya rishtedaar ko udhaar de rahe ho aur rupees me saaf number chahiye.",
                 "Aap aisi FD ya bond coupon check kar rahe ho jo simple interest deti hai."],
        "mistakes": ["Flat rate ko loan ki asli cost maan lena. Reducing balance par flat 10% lagbhag 18% ke barabar hota hai.",
                     "Lambi period par simple aur compound mix kar dena. 10 saal me farak chhota nahi hota.",
                     "Threshold se upar interest par TDS bhoolna, jo actually milne wali raqam kam kar deta hai."],
    },
    "fd": {
        "what": "Fixed deposit ek fixed rate, fixed term ke liye deti hai, aur nateeje ko asli badalne wala decision sirf ek hai - interest reinvest ho raha hai ya nahi. 1,00,000 rupaye 7% par 5 saal me simple terms me 35,000 deta hai, par 40,255 agar interest quarterly compound ho - aur banks default me quarterly compound karte hain. Calculator dono dikhata hai, saath me post-tax figure, kyunki 40,000 rupaye saalana interest se upar TDS hi 7% FD ko 30% slab wale ke liye lagbhag 4.9% bana deta hai.",
        "formula": "Maturity = P x (1 + r / n)^(n x t), jahan r annual rate, n saal me compounds (quarterly ke liye 4) aur t saal. Interest = Maturity - P.",
        "when": ["Aap lump sum park kar rahe ho aur advertised rate nahi, post-tax maturity chahiye.",
                 "Bank FD ko us small-finance bank FD se compare kar rahe ho jo 0.5-1% zyada deta hai.",
                 "3 saal aur 5 saal ki FD me choose kar rahe ho aur rupee ka farak chahiye."],
        "mistakes": ["FD rate ko equity fund ke return se compare karna. FD contractual hai; fund nahi.",
                     "TDS ignore karna. 30% slab wale ke liye FD ka asli return lagbhag rate minus 30% hota hai.",
                     "FD beech me todna bina penalty dekhe - aksar rate ka 0.5-1% lagta hai."],
    },
    "rd": {
        "what": "Recurring deposit har mahine ek hi rate par commitment hai, aur bank har instalment par us din se interest deta hai. 5,000 rupaye mahina 5 saal 7% par lagbhag 3.6 lakh banta hai, jisme 3 lakh aapka hi paisa hai. Ye deposits ka SIP jaisa hai, aur calculator ka kaam interest ko contributions se alag dikhana hai taaki return imaandaar lage.",
        "formula": "Maturity = sum of P x (1 + r / 4)^(bache quarters), har monthly instalment par. Interest = Maturity - (P x mahine).",
        "when": ["Aapko fixed-return monthly habit chahiye aur commit karne se pehle maturity jaanna hai.",
                 "3 saal ke goal ke liye RD ko debt mutual fund se compare kar rahe ho.",
                 "Aap dekhna chahte ho ki aakhri instalment pehli se kitna kamati hai - farak logon ko chauka deta hai."],
        "mistakes": ["Advertised rate poore balance par lagne ki ummeed rakhna. Har instalment sirf utne hi time kamata hai jitna wo andar hai.",
                     "Instalment miss karke penalty na maan lena. Bank lagata hai, aur rate reset ho sakta hai.",
                     "10 saal ke goal ke liye RD use karna. Itne horizon par equity compounding usually jeet jati hai."],
    },
    "wc": {
        "what": "Working capital wo paisa hai jo business ke rozana kaam me bandha hota hai: shelf par stock, plus jo customers aapko dena hai, minus jo aap suppliers ko dena hai. Business profitable ho sakta hai aur phir bhi cash khatam ho jaye, kyunki profit accounting ka number hai aur working capital cash ka. Calculator teen lines ko ek figure aur ek cycle length me badal deta hai, taaki dikhe ki aapka paisa kitne din ghoom kar wapas aata hai.",
        "formula": "Working Capital = Current Assets - Current Liabilities. Cash Conversion Cycle = Days Inventory + Days Receivable - Days Payable.",
        "when": ["Aap profitable ho par bank account baar-baar zero hota hai aur dekhna hai paisa kahan baitha hai.",
                 "Customer 60 din ki terms maangta hai aur aapko uska cost price karna hai.",
                 "Aap working-capital limit ke liye apply kar rahe ho aur bank jo number poochega wo chahiye."],
        "mistakes": ["Sirf stock ginna aur receivables bhoolna. Slow-paying customers slow stock se zyada cash bandhte hain.",
                     "Negative working capital ko hamesha kharab maanna. Prepaid plans wale subscription business ke liye ye healthy hai.",
                     "Cycle length ignore karna. 50 lakh 90 din ke liye bandha aur wahi raqam 15 din ke liye - do alag business hain."],
    },
    "momyoy": {
        "what": "Month-on-month is mahine ko pichhle mahine se compare karta hai. Year-on-year is mahine ko pichhle saal ke usi mahine se. Lagbhag har Indian business ke liye YoY imaandaar number hai, kyunki Diwali, monsoon aur school calendar demand ko itna hilate hain ki MoM zyada tar festival naapta hai, business nahi. Calculator dono deta hai, aur dono ka gap hi seasonality hai.",
        "formula": "MoM % = (This Month - Last Month) / Last Month x 100. YoY % = (This Month - Same Month Last Year) / Same Month Last Year x 100.",
        "when": ["Ek mahina kharab lagta hai aur jaanna hai ki seasonality hai ya asli decline.",
                 "Investor ko present karna hai aur festive distortion ke bina growth dikhani hai.",
                 "Agle quarter ka target set kar rahe ho aur seasonal baseline chahiye."],
        "mistakes": ["Festive mahine ki MoM growth ko trend bata dena. October hamesha September se upar hota hai.",
                     "31 din ke mahine ko 28 din wale se bina days normalise kiye compare karna.",
                     "Ek saal se chhote business par YoY lagana - compare karne ke liye kuch hai hi nahi."],
    },
}


def main() -> None:
    for rel, data in (("tools/tool_guides.json", EN),
                      ("tools/tool_guides_hinglish.json", HI)):
        p = ROOT / rel
        d = json.loads(p.read_text(encoding="utf-8"))
        for cid, guide in data.items():
            d["calcs"][cid] = guide
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{rel} -> {len(d['calcs'])} guides")


if __name__ == "__main__":
    main()
