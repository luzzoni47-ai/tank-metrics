"""Generate the blog Hinglish blocks from the Hindi source.

The posts used to carry three language blocks: English, Hindi and Hinglish.
The site only ships English and Hinglish, so the Hindi source now lives in
``tools/hindi/*.hi.html`` and this script romanises it into the Hinglish block.
Keeping the Hindi as the source means the Hinglish text is regenerated from one
authoritative copy instead of being hand-maintained.

Usage:
    python3 tools/hinglish.py --sample 12     # eyeball quality
    python3 tools/hinglish.py --rebuild       # rewrite the Hinglish blocks
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / 'public' / 'site'
HINDI = ROOT / 'tools' / 'hindi'

POSTS = [
    'blog-what-is-ebitda.html',
    'blog-ltv-cac-ratio-explained.html',
    'blog-startup-valuation-explained.html',
    'blog-burn-rate-runway-guide.html',
    'blog-marketplace-fees-explained.html',
    'blog-markup-vs-margin-explained.html',
    'blog-break-even-point-explained.html',
]

VIRAMA = '्'
NUKTA = '़'
ANUSVARA = 'ंँ'
LABIALS = 'पफबभम'

# --- transliteration tables -------------------------------------------------
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
    'ष': 'sh', 'स': 's', 'ह': 'h', 'ळ': 'l', 'ऱ': 'r',
}

# Nukta letters are two code points (base + ़) and must be matched first.
NUKTA_CONSONANTS = {
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z',
    'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f', 'य़': 'y',
}

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ऍ': 'e', 'ऑ': 'o', 'ऎ': 'e', 'ऒ': 'o',
}

MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ॉ': 'o', 'ॅ': 'e', 'ॆ': 'e', 'ॊ': 'o',
}

SIGNS = {'ं': 'n', 'ँ': 'n', 'ः': 'h', 'ऽ': "'"}

CONJUNCTS = {
    'क्ष': 'ksh', 'ज्ञ': 'gy', 'त्र': 'tr', 'श्र': 'shr',
    'क्र': 'kr', 'प्र': 'pr', 'ब्र': 'br', 'ग्र': 'gr', 'द्र': 'dr', 'द्व': 'dv',
    'श्व': 'shv', 'स्व': 'sv', 'त्य': 'ty', 'द्य': 'dy', 'ह्य': 'hy',
    'र्य': 'ry', 'न्य': 'ny', 'म्य': 'my', 'व्य': 'vy', 'ल्य': 'ly',
    'स्त': 'st', 'स्थ': 'sth', 'स्प': 'sp', 'स्क': 'sk', 'स्ट': 'st',
    'न्द': 'nd', 'म्ब': 'mb', 'म्प': 'mp', 'ङ्ग': 'ng', 'ञ्च': 'nch',
    'च्च': 'chch', 'ट्ट': 'tt', 'त्त': 'tt', 'क्क': 'kk', 'ग्ग': 'gg',
    'प्प': 'pp', 'ब्ब': 'bb', 'ल्ल': 'll', 'म्म': 'mm', 'न्न': 'nn',
    'क्ट': 'kt', 'क्स': 'ks', 'ण्ड': 'nd', 'ण्ण': 'nn', 'ल्ड': 'ld',
    'र्ट': 'rt', 'र्न': 'rn', 'र्म': 'rm', 'र्श': 'rsh', 'र्ष': 'rsh',
    'र्व': 'rv', 'र्ज': 'rj', 'र्ड': 'rd', 'र्स': 'rs', 'र्क': 'rk',
    'र्ग': 'rg', 'र्त': 'rt', 'र्थ': 'rth', 'र्ध': 'rdh', 'र्ब': 'rb',
    'र्ल': 'rl', 'र्ह': 'rh',
}

# The mechanical rules cannot delete the Hindi schwa, cannot tell an English
# loanword from a Hindi one, and spell a few letters the long way. These words
# are simply written the way a Hinglish reader expects to see them.
OVERRIDES = {
    # function words and the highest-frequency vocabulary
    'है': 'hai', 'हैं': 'hain', 'में': 'mein', 'से': 'se', 'और': 'aur',
    'पर': 'par', 'नहीं': 'nahi', 'के': 'ke', 'का': 'ka', 'की': 'ki',
    'यह': 'yeh', 'या': 'ya', 'एक': 'ek', 'तो': 'to', 'जो': 'jo',
    'आम': 'aam', 'कम': 'kam', 'भी': 'bhi', 'वह': 'woh', 'वो': 'wo',
    'क्या': 'kya', 'पहले': 'pehle', 'होता': 'hota', 'असली': 'asli',
    'कि': 'ki', 'को': 'ko', 'करें': 'karein', 'सबसे': 'sabse', 'तौर': 'taur',
    'कुछ': 'kuch', 'ज़्यादा': 'zyada', 'ज्यादा': 'zyada', 'हर': 'har',
    'अपने': 'apne', 'इसे': 'ise', 'आप': 'aap', 'यानी': 'yani',
    'आपका': 'aapka', 'आपके': 'aapke', 'आपकी': 'aapki', 'आपको': 'aapko',
    'आपने': 'aapne', 'टैक्स': 'tax', 'दो': 'do', 'ही': 'hi', 'हो': 'ho',
    'लिए': 'liye', 'इसलिए': 'isliye', 'क्योंकि': 'kyunki', 'बाद': 'baad',
    'निकालें': 'nikalein', 'सकता': 'sakta', 'सकते': 'sakte', 'बात': 'baat',
    'अगर': 'agar', 'निवेश': 'nivesh', 'निवेशक': 'niveshak',
    'निवेशकों': 'niveshakon', 'हिस्सेदारी': 'hissedari', 'राउंड': 'round',
    'आसान': 'aasan', 'भाषा': 'bhasha', 'मतलब': 'matlab', 'काम': 'kaam',
    'कितना': 'kitna', 'कितने': 'kitne', 'कितनी': 'kitni', 'कमाता': 'kamata',
    'बीच': 'beech', 'बना': 'bana', 'चाहते': 'chahte', 'थे': 'the',
    'तुलना': 'tulna', 'बिना': 'bina', 'शोर': 'shor', 'कहाँ': 'kahan',
    'दिखाया': 'dikhaya', 'तरीके': 'tarike', 'तरीका': 'tarika',
    'दोनों': 'dono', 'जवाब': 'jawab', 'ऊपर': 'upar', 'नीचे': 'neeche',
    'मुनाफ़ा': 'munafa', 'मुनाफ़े': 'munafe', 'उदाहरण': 'udaharan',
    'मान': 'maan', 'लीजिए': 'lijiye', 'छोटा': 'chhota', 'छोटी': 'chhoti',
    'चलाते': 'chalate', 'ब्याज': 'byaj', 'भाग': 'bhaag', 'दें': 'dein',
    'मिलता': 'milta', 'परवाह': 'parwah', 'करते': 'karte', 'सवाल': 'sawal',
    'कोशिश': 'koshish', 'पैसा': 'paisa', 'पैसे': 'paise', 'रहा': 'raha',
    'जाँचें': 'jaanchein', 'सेकंडों': 'secondon', 'मुफ़्त': 'muft',
    'सेव': 'save', 'खोलें': 'kholen', 'पता': 'pata', 'होते': 'hote',
    'पूरा': 'pura', 'नाम': 'naam', 'दिखाता': 'dikhata', 'हटा': 'hata',
    'अब': 'ab', 'चीज़ें': 'cheezein', 'चीजें': 'cheezein',
    'किराया': 'kiraya', 'इस्तेमाल': 'istemal', 'वाला': 'wala', 'वाले': 'wale',
    'वाली': 'wali', 'वालों': 'walon', 'साल': 'saal', 'दिन': 'din',
    'नकद': 'nakad', 'बढ़': 'badh', 'दाम': 'daam', 'लागत': 'lagat',
    'मार्जिन': 'margin', 'फ़ायदा': 'fayda', 'फायदा': 'fayda',
    'नुकसान': 'nuksan', 'अंतर': 'antar', 'ज़रूरत': 'zaroorat',
    'जरूरत': 'zaroorat', 'तैयार': 'taiyar', 'मिलेगा': 'milega',
    'करना': 'karna', 'करने': 'karne', 'करता': 'karta', 'करती': 'karti',
    'होगा': 'hoga', 'होगी': 'hogi', 'होना': 'hona', 'होती': 'hoti',
    'रुपये': 'rupaye', 'पूंजी': 'poonji', 'बढ़िया': 'badhiya',
    'सीधा': 'seedha', 'सीधे': 'seedhe', 'नंबर': 'number', 'सब': 'sab',
    'कभी': 'kabhi', 'जब': 'jab', 'तब': 'tab', 'कैसे': 'kaise',
    'हम': 'hum', 'मैं': 'main', 'पढ़ें': 'padhein', 'समझें': 'samjhein',
    'चलिए': 'chaliye', 'देखें': 'dekhein', 'बताएँ': 'batayein',
    'अपना': 'apna', 'अपनी': 'apni', 'हिस्सा': 'hissa', 'क्यों': 'kyon',
    'बहुत': 'bahut', 'थोड़ा': 'thoda', 'जल्दी': 'jaldi', 'याद': 'yaad',
    'रखें': 'rakhein', 'खर्च': 'kharch', 'ग्राहक': 'grahak',
    'ग्राहकों': 'grahakon', 'महीने': 'mahine', 'महीना': 'mahina',
    'महीनों': 'mahinon', 'पहली': 'pehli', 'आंकड़े': 'aankde',
    'आंकड़ा': 'aankda', 'आंकड़ों': 'aankdon', 'कारोबार': 'karobar',
    'कारोबारी': 'karobari', 'कारोबारों': 'karobaron',
    'कारोबारियों': 'karobariyon', 'रहता': 'rehta', 'रहते': 'rehte',
    'रहना': 'rehna', 'कहना': 'kehna', 'कहने': 'kehne',
    'जोड़ना': 'jodna', 'जोड़ने': 'jodne', 'छोड़ने': 'chhodne',
    'टूटने': 'tootne', 'जितने': 'jitne', 'जितना': 'jitna',
    'उतना': 'utna', 'उतनी': 'utni', 'इतनी': 'itni',
    'रुकता': 'rukta', 'रुकते': 'rukte', 'जिसमें': 'jismein',
    'इनमें': 'inmein', 'उससे': 'usse', 'चाहिए': 'chahiye',
    'पूछते': 'poochhte', 'पहुँचते': 'pahunchte', 'खींचते': 'kheenchte',
    'निकलती': 'nikalti', 'चलती': 'chalti', 'पड़ती': 'padti',
    'बदलनी': 'badalni', 'पतला': 'patla', 'अगली': 'agli', 'नई': 'nayi',
    'कई': 'kai', 'मानना': 'maanna', 'टालना': 'talna', 'रोकना': 'rokna',
    'खरीदना': 'khareedna', 'बराबरी': 'barabari', 'टिकाऊ': 'tikaau',
    'आएगी': 'aayegi', 'तुरंत': 'turant', 'बेहतर': 'behtar',
    'सामान्य': 'samanya', 'उलटा': 'ulta', 'लोकप्रिय': 'lokpriya',
    'बेढंगे': 'bedhange', 'छूतीं': 'chhooti', 'साइन': 'sign',
    'बातचीत': 'baatcheet', 'लक्ष्य': 'lakshya', 'मुख्य': 'mukhya',
    'स्वस्थ': 'swasth', 'तथ्य': 'tathya', 'ऋणात्मक': 'rinatmak',
    'गलतफ़हमी': 'galatfehmi', 'नज़रअंदाज़': 'nazarandaz',
    'मौजूदा': 'maujooda', 'अंदाज़ा': 'andaza', 'गुणा': 'guna',
    'बीमा': 'bima', 'ईमानदार': 'imandar', 'ईमानदारी': 'imandari',
    'आशावादी': 'aashavadi', 'ज़्यादातर': 'zyadatar', 'डेटा': 'data',
    'कोई': 'koi', 'कोई': 'koi', 'हिंदी': 'hindi', 'शब्द': 'shabd',
    'आएँ': 'aayein', 'माँगता': 'maangta', 'निकालने': 'nikalne',
    'सालाना': 'saalana', 'मोटा': 'mota', 'मोटे': 'mote',
    'दिखता': 'dikhta', 'दिखते': 'dikhte', 'कहता': 'kehta',
    'कहते': 'kehte', 'लेता': 'leta', 'लेते': 'lete', 'देता': 'deta',
    'देते': 'dete', 'जाता': 'jaata', 'जाती': 'jaati', 'जाते': 'jaate',
    'हुआ': 'hua', 'गया': 'gaya', 'किया': 'kiya', 'लिया': 'liya',
    'दिया': 'diya', 'बताया': 'bataya', 'सोचा': 'socha', 'मिला': 'mila',
    'बना': 'bana', 'चला': 'chala', 'लगा': 'laga', 'रही': 'rahi',
    'गई': 'gayi', 'दिए': 'diye', 'किए': 'kiye', 'हुए': 'hue',
    'रहे': 'rahe', 'गए': 'gaye', 'बचा': 'bacha', 'बचे': 'bache',
    'घटा': 'ghata', 'दिखा': 'dikha', 'बता': 'bata', 'लगे': 'lage',
    'रखे': 'rakhe', 'बदले': 'badle', 'चले': 'chale', 'मिले': 'mile',
    'पड़े': 'pade', 'बढ़े': 'badhe', 'हट': 'hat', 'जा': 'ja', 'दे': 'de',
    'ले': 'le', 'कर': 'kar', 'बन': 'ban', 'खो': 'kho', 'चल': 'chal',
    'रुक': 'ruk', 'मिल': 'mil', 'चुन': 'chun', 'सोच': 'soch',
    'देख': 'dekh', 'दिख': 'dikh', 'कह': 'keh', 'पढ़': 'padh',
    'समझ': 'samajh', 'रख': 'rakh', 'बत': 'bat', 'हो': 'ho', 'जीत': 'jeet',
    'निकल': 'nikal', 'बदल': 'badal', 'बढ़ा': 'badha', 'घटा': 'ghata',
    # participles and other forms that must lose the final schwa
    'बताता': 'batata', 'बताते': 'batate', 'बताना': 'batana',
    'बताए': 'bataye', 'बताएँ': 'batayein', 'बताया': 'bataya',
    'निकलता': 'nikalta', 'निकलती': 'nikalti', 'निकलते': 'nikalte',
    'निकलेगा': 'niklega', 'चलता': 'chalta', 'चलती': 'chalti',
    'चलते': 'chalte', 'चलेगा': 'chalega', 'चलेंगे': 'chalenge',
    'लगता': 'lagta', 'लगती': 'lagti', 'लगते': 'lagte', 'लगेगा': 'lagega',
    'लगाएँ': 'lagayein', 'लगाएँगे': 'lagaenge', 'लायक': 'layak',
    'पड़ेगा': 'padega', 'पड़ेगी': 'padegi', 'पड़ी': 'padi',
    'बढ़ता': 'badhta', 'बढ़ती': 'badhti', 'बढ़ते': 'badhte',
    'बढ़ाती': 'badhati', 'बढ़ाने': 'badhane', 'बढ़ाएँ': 'badhayein',
    'बढ़ोतरी': 'badhotri', 'बढ़ने': 'badhne', 'बदलता': 'badalta',
    'बदलते': 'badalte', 'बदलाव': 'badlav', 'बदलें': 'badlein',
    'दिखाता': 'dikhata', 'दिखाती': 'dikhati', 'दिखाना': 'dikhana',
    'दिखाने': 'dikhane', 'दिखाएँ': 'dikhayein', 'दिखेगा': 'dikhega',
    'हटाती': 'hatati', 'घटता': 'ghatta', 'घटाना': 'ghatana',
    'काटें': 'katein', 'काटते': 'katte', 'जुड़ता': 'judta',
    'जोड़ें': 'jodein', 'जोड़ा': 'joda', 'लौटाता': 'lautata',
    'लौटने': 'lautne', 'मिलाना': 'milana', 'मिलने': 'milne',
    'मिलकर': 'milkar', 'बनाता': 'banata', 'बनाती': 'banati',
    'बनाते': 'banate', 'बनाने': 'banane', 'बनाएँ': 'banayein',
    'जानता': 'jaanta', 'जानते': 'jaante', 'जाने': 'jaane',
    'जानें': 'jaanein', 'जाँचते': 'jaanchte', 'जाँचें': 'jaanchein',
    'सुधारें': 'sudharein', 'सुधार': 'sudhar', 'रुकें': 'rukein',
    'रुकते': 'rukte', 'रुकता': 'rukta', 'सोचें': 'sochein',
    'सोचने': 'sochne', 'समझकर': 'samajhkar', 'समझने': 'samajhne',
    'पूछें': 'poochein', 'पूछे': 'pooche', 'पूछता': 'poochhta',
    'पूछेंगे': 'poochhenge', 'बताएँगे': 'batayenge',
    'मानें': 'maanein', 'माने': 'maane', 'माना': 'maana',
    'चाहें': 'chaahein', 'चाहे': 'chaahe', 'रखता': 'rakhta',
    'रखते': 'rakhte', 'रखे': 'rakhe', 'रहें': 'rahein',
    'देखता': 'dekhta', 'देखते': 'dekhte', 'देखे': 'dekhe',
    'लेकर': 'lekar', 'देकर': 'dekar', 'करके': 'karke',
    'आंकड़े': 'aankde', 'आंकड़ा': 'aankda', 'आंकड़ों': 'aankdon',
    'बाज़ार': 'bazaar', 'बाजार': 'bazaar', 'हिसाब': 'hisaab',
    'सालाना': 'saalana', 'आमदनी': 'aamdani', 'मायने': 'maayne',
    'यहाँ': 'yahaan', 'वहाँ': 'wahaan', 'गलतियाँ': 'galatiyaan',
    'बातें': 'baatein', 'शर्तें': 'shartein', 'शर्तों': 'sharton',
    'बातों': 'baaton', 'रास्ते': 'raaste', 'रिसाव': 'risaav',
    'रुझान': 'rujhaan', 'समाधान': 'samadhan', 'समझदार': 'samajhdar',
    'असरदार': 'asardar', 'लायक': 'layak', 'हालत': 'haalat',
    'संभाला': 'sambhala', 'मानना': 'maanna', 'माँगता': 'maangta',
    'शुरुआती': 'shuruaati', 'शुरू': 'shuru', 'लाएँ': 'laayein',
    'डिस्काउंट': 'discount', 'पड़ाव': 'padaav',
    'अच्छा': 'achha', 'अच्छे': 'achhe', 'अच्छी': 'achhi',
    'कमाई': 'kamai', 'कमाएँ': 'kamayein', 'कमाए': 'kamaye',
    'घटाएँ': 'ghatayein', 'घटाए': 'ghataye', 'जाएँगे': 'jayenge',
    'जाएँ': 'jayein', 'जाए': 'jaye', 'आए': 'aaye', 'आएँ': 'aayein',
    'गुंजाइश': 'gunjaish', 'पहुँच': 'pahunch', 'टिकाऊ': 'tikaau',
    'खींचते': 'kheenchte', 'जाँचते': 'jaanchte', 'पूछते': 'poochhte',
    'लक्ष्य': 'lakshya', 'शुरुआती': 'shuruaati', 'हिस्सेदार': 'hissedar',
    'टूटता': 'tootta', 'टूटती': 'tootti',
    'गलती': 'galat', 'गलतियाँ': 'galatiyaan', 'गलत': 'galat',
    'गाड़ी': 'gaadi', 'गाड़ियाँ': 'gaadiyan',
    'कमज़ोरी': 'kamzori', 'कमज़ोर': 'kamzor',
    'बनाम': 'banam', 'बाकी': 'baaki', 'सीढ़ी': 'seedhi',
    'सीढ़ियाँ': 'seedhiyan', 'रुपया': 'rupaya',
    'साफ़': 'saaf', 'साफ': 'saaf', 'फ़र्क़': 'farq', 'फर्क': 'farq',
    'फ़र्क': 'farq', 'टिका': 'tika', 'न': 'na',
    'भरोसा': 'bharosa', 'भरोसे': 'bharose', 'ताकत': 'taakat',
    'फ़ीस': 'fees', 'फीस': 'fees', 'मेहनत': 'mehnat',
    'पहला': 'pehla', 'पहले': 'pehle', 'पहली': 'pehli',
    'समझाते': 'samjhate', 'समझाता': 'samjhata', 'समझाती': 'samjhati',
    'समझाएँ': 'samjhein', 'समझाना': 'samjhana', 'समझें': 'samjhein',
    'छोड़ता': 'chhodta', 'छोड़ती': 'chhodti', 'छोड़ते': 'chhodte',
    'देखना': 'dekhna', 'देखता': 'dekhta', 'देखते': 'dekhte', 'देखती': 'dekhti',
    'चाहता': 'chahta', 'चाहते': 'chahte', 'चाहती': 'chahti', 'चाहिए': 'chahiye',
    'कहेंगे': 'kahenge', 'कहेंगी': 'kahengi', 'कहता': 'kahta', 'कहते': 'kahte',
    'कसौटी': 'kasauti', 'ग्राहक': 'graahak', 'ग्राहकों': 'graahakon',
    'रुकती': 'rukti', 'रुकता': 'rukta', 'अगला': 'agla', 'अगले': 'agle',
    'अगली': 'agli', 'तेज़ी': 'tezi', 'तेजी': 'tezi',
    'बची': 'bachi', 'बचा': 'bacha', 'बचे': 'bache', 'महँगा': 'mehanga',
    'कहेगी': 'kahegi', 'कहेगा': 'kahega', 'संख्या': 'sankhya',
    'हैरान': 'hairaan', 'पड़ता': 'padta', 'पड़ती': 'padti', 'पड़े': 'pade',
    'सकें': 'saken', 'सके': 'sake', 'बताने': 'bataane', 'बताएँ': 'bataayein',
    'बही': 'bahi', 'बुरी': 'buri', 'बुरा': 'bura',
    'वही': 'wahi', 'यही': 'yahi', 'वहीं': 'wahin', 'यहीं': 'yahin',
    'वे': 've', 'उसी': 'usi', 'इन्हें': 'inhein', 'उन्हें': 'unhein',
    'सबको': 'sabko', 'किसी': 'kisi', 'उसे': 'use', 'उस': 'us',
    'उसकी': 'uski', 'इसकी': 'iski', 'इनके': 'inke', 'उसका': 'uska',
    # English loanwords that the rules would spell phonetically
    'अकाउंटेंट': 'accountant', 'अकाउंटिंग': 'accounting',
    'विभाग': 'vibhag', 'कंपनी': 'company', 'रजिस्टर': 'register',
    'बिज़नेस': 'business', 'बिजनेस': 'business', 'बिज़नस': 'business',
    'कानूनी': 'kanooni', 'कानून': 'kanoon', 'फ़ॉर्मूला': 'formula',
    'फॉर्मूला': 'formula', 'प्रोडक्ट': 'product', 'बैलेंस': 'balance',
    'ऑर्डर': 'order', 'ऑफ़र': 'offer', 'ऑफ़िस': 'office',
    'सर्विस': 'service', 'कमीशन': 'commission', 'इनवॉइस': 'invoice',
    'कॉन्ट्रैक्ट': 'contract', 'सॉफ़्टवेयर': 'software',
    'फ़िज़िकल': 'physical', 'स्टाफ़': 'staff', 'फ़ाउंडर': 'founder',
    'फ़्रीलांसर': 'freelancer', 'एजेंसी': 'agency', 'बैंक': 'bank',
    'मशीन': 'machine', 'मशीनरी': 'machinery', 'शेयर': 'share',
    'शेयरधारक': 'shareholder', 'चैनल': 'channel', 'चैनलों': 'channels',
    'पेजों': 'pages', 'अपडेट': 'update', 'बोनस': 'bonus',
    'ब्राउज़र': 'browser', 'ब्रांड': 'brand', 'सैलरी': 'salary',
    'मार्केटिंग': 'marketing', 'मीटिंग': 'meeting', 'टूल्स': 'tools',
    'सेकंड': 'second', 'टीम': 'tim', 'पेइंग': 'paying',
    'आउट': 'out', 'फ़ाइनल': 'final', 'रणनीतिक': 'strategic',
    'विज्ञान': 'vigyan', 'विज्ञापन': 'vigyapan',
    'बैंगलोर': 'Bangalore', 'गाइड': 'guide', 'हिंदी': 'hindi',
    # marketplace-fees post: the rules misplace the schwa or the vowel on these
    'ऑनलाइन': 'online', 'बिक्री': 'bikri', 'बिकने': 'bikne',
    'वापसी': 'vaapasi', 'चौथाई': 'chauthai', 'बनाना': 'banana',
    'इसी': 'isi', 'करनी': 'karni', 'छीनती': 'chheenti',
    'बचाएँ': 'bachayein', 'बचता': 'bachta', 'सस्ती': 'sasti',
    'ग्राम': 'gram', 'डालने': 'daalne', 'चौंकाता': 'chaunkata',
    'धीमे': 'dheeme', 'पढ़ता': 'padhta', 'पढ़ना': 'padhna',
    'लंबी': 'lambi', 'जोड़कर': 'jodkar', 'पतले': 'patle',
    'अकेले': 'akele', 'रकम': 'rakam', 'हाथ': 'haath',
}

DEVANAGARI = re.compile(r'[\u0900-\u097F]+')


def _tidy(text: str) -> str:
    """Collapse the vowel pile-ups the mechanical rules produce."""
    text = re.sub(r'aaa+', 'aa', text)
    text = re.sub(r'eee+', 'ee', text)
    text = re.sub(r'ooo+', 'oo', text)
    text = re.sub(r'([bcdfghjklmnpqrstvwxyz])\1{2,}', r'\1\1', text)
    if len(text) > 3 and text.endswith('ee') and text[-3] not in 'aeiou':
        text = text[:-1]          # aapakee -> aapaki, chhotee -> chhoti
    if len(text) > 3 and text.endswith('aa') and text[-3] not in 'aeiou':
        text = text[:-1]          # jaataa -> jaata, huaa -> hua
    return text


def _romanise_word(word: str) -> str:
    """Transliterate one Devanagari word to Roman script."""
    if word in OVERRIDES:
        return OVERRIDES[word]

    out: list[str] = []
    i = 0
    n = len(word)
    while i < n:
        two = word[i : i + 2]

        if two in NUKTA_CONSONANTS or two in CONJUNCTS:
            table = NUKTA_CONSONANTS if two in NUKTA_CONSONANTS else CONJUNCTS
            out.append(table[two])
            i += 2
            if i < n and word[i] == VIRAMA:
                i += 1
                continue
            if i < n and word[i] in MATRAS:
                continue
            if i >= n:
                continue          # word-final conjunct drops the inherent vowel
            out.append('a')
            continue

        ch = word[i]

        if ch in CONSONANTS:
            out.append(CONSONANTS[ch])
            i += 1
            if i < n and word[i] == VIRAMA:
                i += 1
                continue
            if i < n and word[i] == NUKTA:
                i += 1
            if i < n and word[i] in MATRAS:
                continue
            if i >= n:
                continue          # Hindi drops the inherent vowel word-finally
            out.append('a')
            continue

        if ch in SIGNS:
            nxt = word[i + 1] if i + 1 < n else ''
            out.append('m' if (ch in ANUSVARA and nxt and nxt in LABIALS) else SIGNS[ch])
            i += 1
            continue

        if ch in VOWELS:
            out.append(VOWELS[ch])
            i += 1
            continue

        if ch in MATRAS:
            out.append(MATRAS[ch])
            i += 1
            continue

        if ch in (VIRAMA, NUKTA):
            i += 1
            continue

        out.append(ch)
        i += 1

    return _tidy(''.join(out))


def to_hinglish(text: str) -> str:
    """Romanise every Devanagari run in a string, leaving Latin text alone."""
    return DEVANAGARI.sub(lambda m: _romanise_word(m.group(0)), text)


BLOCK_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol',
              'div', 'br', 'tr', 'td', 'th', 'blockquote', 'table', 'section'}


def _capitalise(html: str) -> str:
    """Sentence-case the visible text without touching tags or attributes.

    Tags are copied through untouched, but the sentence-start state carries
    across inline tags: ``<strong>नहीं</strong> है`` must not become
    ``Nahi hai``. Block tags do start a new sentence.
    """
    out: list[str] = []
    at_start = True
    i = 0
    n = len(html)
    while i < n:
        if html[i] == '<':
            end = html.find('>', i)
            if end == -1:
                out.append(html[i:])
                break
            tag = html[i : end + 1]
            out.append(tag)
            name = tag.strip('</> \t\n').split()[0].lower() if tag.strip('</> \t\n') else ''
            if name in BLOCK_TAGS:
                at_start = True
            i = end + 1
            continue
        ch = html[i]
        if at_start and ch.isalpha():
            out.append(ch.upper())
            at_start = False
        else:
            out.append(ch)
        if ch in '.!?':
            at_start = True
        elif not ch.isspace() and ch not in '"\u201c\u201d':
            at_start = False
        i += 1
    return ''.join(out)


def _find_block(html: str, start: int) -> int:
    """Return the offset just past the div that starts at ``start``."""
    depth, pos = 0, start
    while pos < len(html):
        nxt = html.find('<div', pos)
        close = html.find('</div>', pos)
        if close == -1:
            raise AssertionError('unbalanced block')
        if nxt != -1 and nxt < close:
            depth += 1
            pos = nxt + 4
        else:
            depth -= 1
            pos = close + 6
            if depth == 0:
                return pos
    raise AssertionError('unbalanced block')


def _drop_hinglish_block(html: str) -> str:
    start = html.find('<div class="post-lang" data-lang="hinglish"')
    if start == -1:
        return html
    return html[:start] + html[_find_block(html, start) :]


def _anchor(html: str) -> str:
    """Return the block the Hinglish copy is inserted after.

    With the Hindi block gone, Hinglish follows the English one. The anchor is
    located by nesting rather than by the next marker, because the English
    block is the last child before the closing tags.
    """
    start = html.find('<div class="post-lang" data-lang="en"')
    assert start != -1, 'no English block found'
    return html[start : _find_block(html, start)]


def build_hinglish_block(hindi_body: str) -> str:
    """Turn the Hindi source into the matching Hinglish block."""
    body = _capitalise(to_hinglish(hindi_body))
    return (
        '<div class="post-lang" data-lang="hinglish" lang="hi-Latn" hidden>'
        + body
        + '</div>'
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--sample', type=int, default=0,
                    help='print N transliterated sentences and exit')
    ap.add_argument('--rebuild', action='store_true',
                    help='write the Hinglish blocks into the posts')
    args = ap.parse_args()

    if args.sample:
        src = (HINDI / (POSTS[0].replace('.html', '.hi.html'))).read_text()
        text = _capitalise(to_hinglish(re.sub(r'<[^>]+>', ' ', src)))
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        for s in sentences[: args.sample]:
            print('-', s)
        return 0

    if args.rebuild:
        for name in POSTS:
            p = SITE / name
            html = _drop_hinglish_block(p.read_text())
            source = (HINDI / name.replace('.html', '.hi.html')).read_text().strip()
            anchor = _anchor(html)
            html = html.replace(anchor, anchor + build_hinglish_block(source), 1)
            p.write_text(html)
            print('hinglish written:', name)
        return 0

    ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
