# 实验结果

实际评测 100 篇；无效文件 4 篇。
所有分数范围 0–1；ROUGE 为逐篇 F1 的平均值；BLEU 为语料级 BLEU-4。

| 方法 | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU-4 | 平均摘要词数 | 平均耗时/秒 |
|---|---:|---:|---:|---:|---:|---:|
| lead-3 | 0.2847 | 0.0939 | 0.1738 | 0.0601 | 71.8 | 0.00083 |
| textrank-overlap | 0.2744 | 0.0840 | 0.1742 | 0.0461 | 93.1 | 0.00291 |
| textrank-tfidf | 0.2839 | 0.0912 | 0.1828 | 0.0566 | 79.6 | 0.00330 |
| overlap-k1 | 0.2424 | 0.0642 | 0.1631 | 0.0421 | 31.8 | 0.00273 |
| lead-1 | 0.2256 | 0.0658 | 0.1556 | 0.0312 | 25.6 | 0.00076 |
| overlap-k2 | 0.2812 | 0.0824 | 0.1793 | 0.0551 | 62.6 | 0.00290 |
| lead-2 | 0.2870 | 0.0968 | 0.1845 | 0.0706 | 49.5 | 0.00079 |
| overlap-k4 | 0.2655 | 0.0903 | 0.1727 | 0.0457 | 120.7 | 0.00283 |
| lead-4 | 0.2792 | 0.0981 | 0.1669 | 0.0568 | 94.0 | 0.00078 |
| overlap-k5 | 0.2471 | 0.0881 | 0.1652 | 0.0426 | 148.2 | 0.00284 |
| lead-5 | 0.2752 | 0.1042 | 0.1686 | 0.0574 | 114.6 | 0.00077 |
| overlap-d0.7 | 0.2753 | 0.0850 | 0.1745 | 0.0458 | 93.4 | 0.00269 |
| overlap-d0.95 | 0.2728 | 0.0855 | 0.1727 | 0.0463 | 92.0 | 0.00292 |

## 结果解读

相同句数仍可能产生不同词数，因此应结合摘要长度解读指标。Lead 基线利用新闻开头的信息；图排序偏向与其他句子共享词汇的句子，不能保证抓住关键事件。
本次运行属于固定配置评测；参数扫描属于同一批数据上的探索性分析，没有训练或独立调参测试划分，不能作为调参后的独立测试结论。
ROUGE/BLEU 衡量词面重合，不能直接判断事实正确性和指代连贯性。ROUGE-BE 未实现。

## 固定案例（输入顺序前三篇）

### 02887117a166b724f3e086138f91715c505c724d / lead-3

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Investigators arrested Lohan on suspicion of domestic violence after an incident on Monday night , but they let him out of jail after he posted bail .

原文句子下标（从 0 开始）：[0, 1, 2]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / lead-3

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：( CNN ) -- The first nine months of this year has seen more pirate attacks than all of last year . And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . The increase in attacks has forced many countries to patrol pirate hotspots such as the Gulf of Aden .

原文句子下标（从 0 开始）：[0, 1, 2]

### 066434e382fd3567927ce858b213b0b1338577a5 / lead-3

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Iranian law requires all women to cover their hair , regardless of their religion .

原文句子下标（从 0 开始）：[0, 1, 2]

### 02887117a166b724f3e086138f91715c505c724d / textrank-overlap

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said .

原文句子下标（从 0 开始）：[0, 1, 4]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / textrank-overlap

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast . With the ransoms they collect , pirates can earn up to $ 40,000 a year , analysts say .

原文句子下标（从 0 开始）：[1, 23, 26]

### 066434e382fd3567927ce858b213b0b1338577a5 / textrank-overlap

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[0, 1, 12]

### 02887117a166b724f3e086138f91715c505c724d / textrank-tfidf

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said . Police responded to a domestic violence call at Michael Lohan 's home Monday and arrested him for the battery of his live-in girlfriend , police said .

原文句子下标（从 0 开始）：[1, 4, 11]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / textrank-tfidf

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast . With the ransoms they collect , pirates can earn up to $ 40,000 a year , analysts say .

原文句子下标（从 0 开始）：[1, 23, 26]

### 066434e382fd3567927ce858b213b0b1338577a5 / textrank-tfidf

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday . They said no punishment was carried out on her , '' he said later Monday .

原文句子下标（从 0 开始）：[0, 12, 19]

### 02887117a166b724f3e086138f91715c505c724d / overlap-k1

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement .

原文句子下标（从 0 开始）：[1]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-k1

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday .

原文句子下标（从 0 开始）：[1]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-k1

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[12]

### 02887117a166b724f3e086138f91715c505c724d / lead-1

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again .

原文句子下标（从 0 开始）：[0]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / lead-1

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：( CNN ) -- The first nine months of this year has seen more pirate attacks than all of last year .

原文句子下标（从 0 开始）：[0]

### 066434e382fd3567927ce858b213b0b1338577a5 / lead-1

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it .

原文句子下标（从 0 开始）：[0]

### 02887117a166b724f3e086138f91715c505c724d / overlap-k2

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement .

原文句子下标（从 0 开始）：[0, 1]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-k2

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast .

原文句子下标（从 0 开始）：[1, 23]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-k2

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[1, 12]

### 02887117a166b724f3e086138f91715c505c724d / lead-2

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement .

原文句子下标（从 0 开始）：[0, 1]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / lead-2

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：( CNN ) -- The first nine months of this year has seen more pirate attacks than all of last year . And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday .

原文句子下标（从 0 开始）：[0, 1]

### 066434e382fd3567927ce858b213b0b1338577a5 / lead-2

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf .

原文句子下标（从 0 开始）：[0, 1]

### 02887117a166b724f3e086138f91715c505c724d / overlap-k4

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said . Police responded to a domestic violence call at Michael Lohan 's home Monday and arrested him for the battery of his live-in girlfriend , police said .

原文句子下标（从 0 开始）：[0, 1, 4, 11]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-k4

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Of the incidents this year , Somali pirates accounted for 54 percent : they launched 168 attacks . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast . With the ransoms they collect , pirates can earn up to $ 40,000 a year , analysts say .

原文句子下标（从 0 开始）：[1, 5, 23, 26]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-k4

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Kian was not able to speak to Ashtiani , and neither the courts nor the prison would confirm the whipping , but he believes the other woman , he said Monday . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[0, 1, 8, 12]

### 02887117a166b724f3e086138f91715c505c724d / lead-4

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Investigators arrested Lohan on suspicion of domestic violence after an incident on Monday night , but they let him out of jail after he posted bail . Just after 1 a.m.

原文句子下标（从 0 开始）：[0, 1, 2, 3]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / lead-4

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：( CNN ) -- The first nine months of this year has seen more pirate attacks than all of last year . And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . The increase in attacks has forced many countries to patrol pirate hotspots such as the Gulf of Aden . `` The increased activity in Somalia is the major reason for the spike , '' said Cyrus Mody , manager of the International Maritime Bureau , which monitors shipping crimes .

原文句子下标（从 0 开始）：[0, 1, 2, 3]

### 066434e382fd3567927ce858b213b0b1338577a5 / lead-4

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Iranian law requires all women to cover their hair , regardless of their religion . The Times of London ran the photo on its front page on August 28 , identifying a woman in it as Ashtiani .

原文句子下标（从 0 开始）：[0, 1, 2, 3]

### 02887117a166b724f3e086138f91715c505c724d / overlap-k5

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said . Lohan called his girlfriend again while she was talking with police , and she put him on speakerphone , it said . Police responded to a domestic violence call at Michael Lohan 's home Monday and arrested him for the battery of his live-in girlfriend , police said .

原文句子下标（从 0 开始）：[0, 1, 4, 5, 11]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-k5

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Of the incidents this year , Somali pirates accounted for 54 percent : they launched 168 attacks . Somalia 's transitional government , which has a tenuous grip on power , has been unable to stop the pirates -- many of whom are based in the port cities . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast . With the ransoms they collect , pirates can earn up to $ 40,000 a year , analysts say .

原文句子下标（从 0 开始）：[1, 5, 10, 23, 26]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-k5

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Kian was not able to speak to Ashtiani , and neither the courts nor the prison would confirm the whipping , but he believes the other woman , he said Monday . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday . He declined to identify the woman who passed the information to Ashtiani 's son , saying it would put her at risk of further harassment by the Iranian authorities .

原文句子下标（从 0 开始）：[0, 1, 8, 12, 13]

### 02887117a166b724f3e086138f91715c505c724d / lead-5

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Investigators arrested Lohan on suspicion of domestic violence after an incident on Monday night , but they let him out of jail after he posted bail . Just after 1 a.m. Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said .

原文句子下标（从 0 开始）：[0, 1, 2, 3, 4]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / lead-5

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：( CNN ) -- The first nine months of this year has seen more pirate attacks than all of last year . And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . The increase in attacks has forced many countries to patrol pirate hotspots such as the Gulf of Aden . `` The increased activity in Somalia is the major reason for the spike , '' said Cyrus Mody , manager of the International Maritime Bureau , which monitors shipping crimes . From January 1 until September 30 , pirates worldwide mounted 306 attacks , compared with 293 in all of 2008 , the Bureau said .

原文句子下标（从 0 开始）：[0, 1, 2, 3, 4]

### 066434e382fd3567927ce858b213b0b1338577a5 / lead-5

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Iranian law requires all women to cover their hair , regardless of their religion . The Times of London ran the photo on its front page on August 28 , identifying a woman in it as Ashtiani . It later apologized , saying it was not her .

原文句子下标（从 0 开始）：[0, 1, 2, 3, 4]

### 02887117a166b724f3e086138f91715c505c724d / overlap-d0.7

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Police responded to a domestic violence call at Michael Lohan 's home Monday and arrested him for the battery of his live-in girlfriend , police said .

原文句子下标（从 0 开始）：[0, 1, 11]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-d0.7

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast . With the ransoms they collect , pirates can earn up to $ 40,000 a year , analysts say .

原文句子下标（从 0 开始）：[1, 23, 26]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-d0.7

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：( CNN ) -- Contradictory reports swirled around the case of an Iranian woman sentenced to be stoned to death for adultery , with one Iranian lawyer saying Monday that she had been whipped 99 times for another alleged offense but another casting doubt on it . A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[0, 1, 12]

### 02887117a166b724f3e086138f91715c505c724d / overlap-d0.95

参考摘要：NEW : Lohan has been admitted for overnight hospital observation , police said Officers say they caught him after a short chase Lohan may have broken his foot and is being evaluated by doctors Michael Lohan jumped off a third-floor balcony to escape arrest , police said

输出摘要：( CNN ) -- Actress Lindsay Lohan 's father jumped from a third-floor balcony Thursday to try to escape re-arrest , police said , but officers soon caught up with him and took him into custody -- again . Officers detained Michael Lohan after his girlfriend , Kate Major , said he violated terms of his release from jail earlier this week by calling her , the Tampa Police Department said in a statement . Thursday , Lohan 's girlfriend called police to say Lohan had violated the terms of his release by calling her , the police statement said .

原文句子下标（从 0 开始）：[0, 1, 4]

### 009de808cb24801b7dc1f85ed875b3d92edbc477 / overlap-d0.95

参考摘要：Somali pirates accounted for 54 percent of all attacks this year Most of them took place off east coast of Somalia and in Gulf of Aden Somali pirates are still holding four ships for ransom Other trouble spots were waters off Nigeria , Malaysia and Bangladesh

输出摘要：And more than half of those attacks were carried out by suspected Somali pirates , an international maritime watchdog group said Wednesday . Of the incidents this year , Somali pirates accounted for 54 percent : they launched 168 attacks . Those who have tracked pirate activity say it started in Somalia in the 1980s , when the pirates claimed they were aiming to stop the rampant illegal fishing and dumping that continues to this day off the Somali coast .

原文句子下标（从 0 开始）：[1, 5, 23]

### 066434e382fd3567927ce858b213b0b1338577a5 / overlap-d0.95

参考摘要：NEW : The Times of London publishes a scathing editorial condemning Iranian authorities An Iranian woman sentenced to be killed was whipped for another offense , a lawyer says He says he heard it from a woman who was in prison with her French foreign minister vows to help Sakineh Mohammadi Ashtiani

输出摘要：A woman who was in prison with Sakineh Mohammadi Ashtiani told lawyer Javid Houtan Kian that his client had been lashed over a newspaper photograph that , Iranian authorities thought , showed her without a headscarf . Kian was not able to speak to Ashtiani , and neither the courts nor the prison would confirm the whipping , but he believes the other woman , he said Monday . Ashtiani asked the woman , who was released from prison , to tell her son she had been whipped , Kian said from Iran on Monday .

原文句子下标（从 0 开始）：[1, 8, 12]