---
layout: default
title:  "rgbctf2020 - Grab your Jisho"
date:   2020-07-19 10:44:11 +0100
categories: rgbctf
---

## **Grab Your Jisho**
Description: 
>これは文字化けか？それとも暗号…？ 

Category: *Crypto*

First Blood: **8 hours, 56 minutes** after release by team **srdnlen**

Repository [here][git-kanjicipher]

### **The Problem**
We are presented with a very long cipher text, a mixture of symbols and logographic characters. Here is a sample from the file:

>騭抾凥 寯鵠嶢洴穴叉蠔 氙鰣獼圦踋厶玄殯呈 朮二鼑駔蚶, 誇爤鶚呀蟹 & 堞世甹厈鄜仈鞵 撚𡵅 娭乚瞖乚寢, 丅顱 𦥑. 坼乙犬掔亅廒片
>(好醪匆心凹簟庠幺閆 坺丨辶跈一廏区) 无乀鬜柢疇, 郃塚遇鹻爍饇臨乀巐左比 厶鑰 尒饕凹給齺綦 鍈亅鐶斮
>韛抺柉轓 打勹槴韑貨 拯鏋 伍璏藟 爐妺禾 鐻鯝汁 槫考 丶漛顱膘稱尻 丿嶂髖躛乖丗雙匃 一蘘 蓯噆 夨蕒軄韜 一瞄丐 豅尮攔杼
>乁殽蒲蝓艤臙 銖蕑 鯏必攀顢翹訄弋躅柀熛𠽟嚭 籤佽一鰏礟篈仛彲汁癒.  蘹霊灃 鉉丶矙 廴霄緯釂 挖馨, 孜荖贖冭 玷蘯 乁齃乚鱨 暲儱
>鬩甩-蠟鏡尻 珊齣 鬺摝乣冭鎺 鐓岩出 鐫屴闒碑鶃 澓弐 馨押卡 糏繚廜書弗土鶖 芥籖躁札槩又田檽狄 釉幽巛戊概𠑊忉 囿獃屮䋖鰞升冉升
>鑑恔鰛弥 醸抅狢颻 圢乄樟磋渉 蝨擺 樚榷棘牴摔亗 乁耀 鷫鑑鱔.床攛闡匛鞁𠘨史霢佣.鼏鎰批
>剿躡譯肯韞 & 瑛匛㐬皮嘈牜韻 罸亥 脂乚燎亅蓼

### **Solution**
The first clue is the title. _Jisho_ is the Japanese word for dictionary and all of these characters are, you guessed it, Japanese Kanji. Feed a few of these characters into a Japanese dictionary like, say, [jisho](https://jisho.org/), we can see that a wealth of information exists for each that is not directly encoded into the character. One such piece of information is the `stroke count`. That is, the amount of pen-strokes needed to draw the character. This is the key to this cipher.

Lets take the first 10 characters and see where the `stroke-count` gets us:

`騭抾凥 寯鵠嶢洴穴叉蠔 氙鰣獼`

becomes

`20 8 5   16 18 15 10 5 3 20   7 21 20`

Starting to look a bit like `a1z26`, no? Decoding as such yields:

`the project gut`

Great. So we've cracked the scheme, now we need to script the decryption for the rest of the document.

### **Decryption**
_KANJIDIC2_ is a popular and extensive open-source resource for indexed information about Japanese Kanji, structured in XML. Download it [here](kanjidic2).

Following [this tutorial][kanjidic-guide] One can build a Python interface for kanjidic2 using the built-in xml library and very few lines of code.

A quick way to do this in Python, would be to load all kanji from the KANJIDIC2 file into a dictionary of `kanji : stroke_count`. See the `get_dict_kanji_stroke` function below:

{% highlight python %}
import xml.etree.ElementTree as ET
TREE = ET.parse('kanjidic2.xml')
ROOT = TREE.getroot()


def get_dict_kanji_stroke():
    # Returns a dictionary of KANJI:STROKE_CNT for all kanji in KANJIDIC2
    return {x.findtext('literal'):x.findtext('misc/stroke_count') for x in ROOT}


def decrypt(cipher):
    stroke_counts = get_dict_kanji_stroke()    
    return "".join([chr(96 + int(stroke_counts[c])) if c in stroke_counts.keys() else c for c in cipher])
{% endhighlight %}

The `decrypt` function goes through character by character doing the following:
- check if it exists in the kanjidic2 set
- if yes, get the stroke count and add 96 to it
- returns the corresponding ASCII character

Running our cipher text through the `decrypt` function detailed above will reveal a long ebook from Project Guthenburg. Searching for the flag yields `rgbctf{~|~yominikui~|~}`. 

### **Encryption**
How did the encryption work?

 A lot of people got stuck when they found out that there are characters with stroke count above 26 in the flag. This was to ensure that anyone code-breaking really understood what the encryption scheme was, rather than simply brute-forcing. These characters `{`, `}`, `~` and `|`, all occur immediately after `z` in ASCII. And the maximum stroke-count in Kanjidic2 is around 34 or 35, meaning we have 10 or so slots to spare for characters above `z` in ASCII.

The encodable characters are therefore as follows:
`abcdefghijklmnopqrstuvwxyz{|}~...`

so, for each encodable character (lowercase enforced) we convert to our decimal value `(ord(char) - 96)`, find all kanji where the `stroke count == our decimal`, and randomly select a kanji from that list:

>a => 1 => random.choice(['一', '乙', '丶', '丿', '亅', '丨', '乀', '乁', '乚'])

>b => 2 => random.choice(['九', '七', '十', '人', '丁', '刀', '二', '入', '乃', '八' ... ])

>c => 3 => random.choice(['下', '干', '丸', '久', '及', '弓', '巾', '己', '乞', '口' ... ])

Here is a Hello World example:
> hello,world! -> 併癶棌傚魴, 𪘚緞織廃𡴭!

And the code used for encryption:
{% highlight python %}
import xml.etree.ElementTree as ET
TREE = ET.parse('kanjidic2.xml')
ROOT = TREE.getroot()


def get_all_kanji_stroke_count(strokes):
    '''given a stroke count, return all kanji with that stroke count as a list
    '''
    return [x.findtext('literal') for x in ROOT if x.findtext('misc/stroke_count') == str(strokes)]


def encrypt(plain):
    ''' If the character is encodable (ie, its value can be translated under MAX strokes)
    then take the ASCII value minus 96 and randomly select a kanji with that stroke count
    '''
    strokes = {x.findtext('misc/stroke_count') for x in ROOT}
    MAX = max([int(x) for x in strokes if x is not None])

    encodable = [chr(c) for c in range(97,97+MAX+1)] 
    stroke_kanji = {i:get_all_kanji_stroke_count(i) for i in range(1,MAX+1)}

    cipher = [random.choice(stroke_kanji[ord(c.lower()) - 96]) if c.lower() in encodable else c.lower() for c in plain]

    return "".join(cipher)
{% endhighlight %}

### **Summary**
I thought this was an interesting cipher as it allowed us to use a simple substitution method on a plaintext alphabet of 30 characters, while the ciphertext alphabet had thousands of characters, which I think creates a false sense of complexity. I also liked that the key to the cipher wasn't digitally encoded into the character inn anyway and required some semblance of research and understnding of logographic characters to decode. 

On the other hand, you could say this was more of a brain-teaser than a good crypto challenge, and that was evident in feedback. Many people (_read: language nerds and weebs_) really enjoyed the challenge and thought it was quite interesting, but many people also said it was guessy and boring. I suppose more hints should have been given? Or perhaps it would have been better suited to the `misc` category? But thats a lesson for the next CTF I write challenges for.

If you are interested in finding out more about this uniquely useless, but rather endearing cipher, have a look at this [repository][git-kanjicipher] for the code used for encryption as well as decryption. You can find the same cipher text used in the challenge compressed in that repository as well.


[git-kanjicipher]: https://github.com/klanec/kanjicipher.git
[kanjidic-guide]: https://aidanenglish.wordpress.com/kanjidic2-parsing-with-python3/
[kanjidic2]: http://www.edrdg.org/kanjidic/kanjidic2.xml.gz