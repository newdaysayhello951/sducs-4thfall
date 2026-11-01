# 实验结果

实际评测 4996 篇；无效文件 4 篇。
所有分数范围 0–1；ROUGE 为逐篇 F1 的平均值；BLEU 为语料级 BLEU-4。

| 方法 | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU-4 | 平均摘要词数 | 平均耗时/秒 |
|---|---:|---:|---:|---:|---:|---:|
| lead-3 | 0.3032 | 0.1113 | 0.1975 | 0.0735 | 72.3 | 0.00081 |
| textrank-overlap | 0.2793 | 0.0914 | 0.1811 | 0.0530 | 92.5 | 0.00276 |
| textrank-tfidf | 0.2842 | 0.0929 | 0.1861 | 0.0576 | 79.3 | 0.00303 |

## 结果解读

相同句数仍可能产生不同词数，因此应结合摘要长度解读指标。Lead 基线利用新闻开头的信息；图排序偏向与其他句子共享词汇的句子，不能保证抓住关键事件。
本次运行属于固定配置评测；参数扫描属于同一批数据上的探索性分析，没有训练或独立调参测试划分，不能作为调参后的独立测试结论。
ROUGE/BLEU 衡量词面重合，不能直接判断事实正确性和指代连贯性。ROUGE-BE 未实现。

## 固定案例（输入顺序前三篇）

### 0001d1afc246a7964130f43ae940af6bc6c57f01 / lead-3

参考摘要：Syrian official : Obama climbed to the top of the tree , `` does n't know how to get down '' Obama sends a letter to the heads of the House and Senate Obama to seek congressional approval on military action against Syria Aim is to determine whether CW were used , not by whom , says U.N. spokesman

输出摘要：It 's official : U.S. President Barack Obama wants lawmakers to weigh in on whether to use military force in Syria . Obama sent a letter to the heads of the House and Senate on Saturday night , hours after announcing that he believes military action against Syrian targets is the right step to take over the alleged use of chemical weapons . The proposed legislation from Obama asks Congress to approve the use of military force `` to deter , disrupt , prevent and degrade the potential for future uses of chemical weapons or other weapons of mass destruction .

原文句子下标（从 0 开始）：[0, 1, 2]

### 0002095e55fcbd3a2f366d9bf92a95433dc305ef / lead-3

参考摘要：Usain Bolt wins third gold of world championship Anchors Jamaica to 4x100m relay victory Eighth gold at the championships for Bolt Jamaica double up in women 's 4x100m relay

输出摘要：( CNN ) -- Usain Bolt rounded off the world championships Sunday by claiming his third gold in Moscow as he anchored Jamaica to victory in the men 's 4x100m relay . The fastest man in the world charged clear of United States rival Justin Gatlin as the Jamaican quartet of Nesta Carter , Kemar Bailey-Cole , Nickel Ashmeade and Bolt won in 37.36 seconds . The U.S finished second in 37.56 seconds with Canada taking the bronze after Britain were disqualified for a faulty handover .

原文句子下标（从 0 开始）：[0, 1, 2]

### 00027e965c8264c35cc1bc55556db388da82b07f / lead-3

参考摘要：The employee in agency 's Kansas City office is among hundreds of `` virtual '' workers The employee 's travel to and from the mainland U.S. last year cost more than $ 24,000 The telecommuting program , like all GSA practices , is under review

输出摘要：Kansas City , Missouri ( CNN ) -- The General Services Administration , already under investigation for lavish spending , allowed an employee to telecommute from Hawaii even though he is based at the GSA 's Kansas City , Missouri , office , a CNN investigation has found . It cost more than $ 24,000 for the business development specialist to travel to and from the mainland United States over the past year . He is among several hundred GSA `` virtual '' workers who also travel to various conferences and their home offices , costing the agency millions of dollars over the past three years .

原文句子下标（从 0 开始）：[0, 1, 2]

### 0001d1afc246a7964130f43ae940af6bc6c57f01 / textrank-overlap

参考摘要：Syrian official : Obama climbed to the top of the tree , `` does n't know how to get down '' Obama sends a letter to the heads of the House and Senate Obama to seek congressional approval on military action against Syria Aim is to determine whether CW were used , not by whom , says U.N. spokesman

输出摘要：It 's official : U.S. President Barack Obama wants lawmakers to weigh in on whether to use military force in Syria . Obama 's remarks came shortly after U.N. inspectors left Syria , carrying evidence that will determine whether chemical weapons were used in an attack early last week in a Damascus suburb . After Obama 's speech , a military and political analyst on Syrian state TV said Obama is `` embarrassed '' that Russia opposes military action against Syria , is `` crying for help '' for someone to come to his rescue and is facing two defeats -- on the political and military levels .

原文句子下标（从 0 开始）：[0, 15, 63]

### 0002095e55fcbd3a2f366d9bf92a95433dc305ef / textrank-overlap

参考摘要：Usain Bolt wins third gold of world championship Anchors Jamaica to 4x100m relay victory Eighth gold at the championships for Bolt Jamaica double up in women 's 4x100m relay

输出摘要：( CNN ) -- Usain Bolt rounded off the world championships Sunday by claiming his third gold in Moscow as he anchored Jamaica to victory in the men 's 4x100m relay . Earlier , Jamaica 's women underlined their dominance in the sprint events by winning the 4x100m relay gold , anchored by Shelly-Ann Fraser-Pryce , who like Bolt was completing a triple . Bolt 's final dash for golden glory brought the eight-day championship to a rousing finale , but while the hosts topped the medal table from the United States there was criticism of the poor attendances in the Luzhniki Stadium .

原文句子下标（从 0 开始）：[0, 8, 16]

### 00027e965c8264c35cc1bc55556db388da82b07f / textrank-overlap

参考摘要：The employee in agency 's Kansas City office is among hundreds of `` virtual '' workers The employee 's travel to and from the mainland U.S. last year cost more than $ 24,000 The telecommuting program , like all GSA practices , is under review

输出摘要：Kansas City , Missouri ( CNN ) -- The General Services Administration , already under investigation for lavish spending , allowed an employee to telecommute from Hawaii even though he is based at the GSA 's Kansas City , Missouri , office , a CNN investigation has found . Dan Tangherlini , who was appointed acting GSA administrator this year , said the agency was examining the cost of the entire teleworking program . Congress launched an investigation into the GSA after a scathing inspector general 's report issued this year showed lavish spending -- $ 823,000 -- at the agency 's Western Regions Conference in Las Vegas in October 2010 .

原文句子下标（从 0 开始）：[0, 15, 26]

### 0001d1afc246a7964130f43ae940af6bc6c57f01 / textrank-tfidf

参考摘要：Syrian official : Obama climbed to the top of the tree , `` does n't know how to get down '' Obama sends a letter to the heads of the House and Senate Obama to seek congressional approval on military action against Syria Aim is to determine whether CW were used , not by whom , says U.N. spokesman

输出摘要：It 's official : U.S. President Barack Obama wants lawmakers to weigh in on whether to use military force in Syria . On Saturday , Obama proposed what he said would be a limited military action against Syrian President Bashar al-Assad . Iran : U.S. military action in Syria would spark ` disaster '

原文句子下标（从 0 开始）：[0, 29, 75]

### 0002095e55fcbd3a2f366d9bf92a95433dc305ef / textrank-tfidf

参考摘要：Usain Bolt wins third gold of world championship Anchors Jamaica to 4x100m relay victory Eighth gold at the championships for Bolt Jamaica double up in women 's 4x100m relay

输出摘要：( CNN ) -- Usain Bolt rounded off the world championships Sunday by claiming his third gold in Moscow as he anchored Jamaica to victory in the men 's 4x100m relay . Earlier , Jamaica 's women underlined their dominance in the sprint events by winning the 4x100m relay gold , anchored by Shelly-Ann Fraser-Pryce , who like Bolt was completing a triple . Germany 's Christina Obergfoll finally took gold at global level in the women 's javelin after five previous silvers , while Kenya 's Asbel Kiprop easily won a tactical men 's 1500m final .

原文句子下标（从 0 开始）：[0, 8, 14]

### 00027e965c8264c35cc1bc55556db388da82b07f / textrank-tfidf

参考摘要：The employee in agency 's Kansas City office is among hundreds of `` virtual '' workers The employee 's travel to and from the mainland U.S. last year cost more than $ 24,000 The telecommuting program , like all GSA practices , is under review

输出摘要：Klumb called the GSA 's teleworking program `` a successful program that 's going to lead to cost savings for taxpayers . And a GSA employee in Kansas City , who requested anonymity , said that hiring someone in Hawaii to work for the Kansas City region was ludicrous . Dan Tangherlini , who was appointed acting GSA administrator this year , said the agency was examining the cost of the entire teleworking program .

原文句子下标（从 0 开始）：[10, 12, 15]