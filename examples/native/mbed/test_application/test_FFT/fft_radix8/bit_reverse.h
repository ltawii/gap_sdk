#ifndef BIT_REVERSE_H
#define BIT_REVERSE_H

#define DATA_LOCATION __attribute__((section(".data_l1")))

DATA_LOCATION short bit_rev_radix8_LUT[FFT_LEN_RADIX8] = {
/*
0,
64,
128,
192,
256,
320,
384,
448,
8,
72,
136,
200,
264,
328,
392,
456,
16,
80,
144,
208,
272,
336,
400,
464,
24,
88,
152,
216,
280,
344,
408,
472,
32,
96,
160,
224,
288,
352,
416,
480,
40,
104,
168,
232,
296,
360,
424,
488,
48,
112,
176,
240,
304,
368,
432,
496,
56,
120,
184,
248,
312,
376,
440,
504,
1,
65,
129,
193,
257,
321,
385,
449,
9,
73,
137,
201,
265,
329,
393,
457,
17,
81,
145,
209,
273,
337,
401,
465,
25,
89,
153,
217,
281,
345,
409,
473,
33,
97,
161,
225,
289,
353,
417,
481,
41,
105,
169,
233,
297,
361,
425,
489,
49,
113,
177,
241,
305,
369,
433,
497,
57,
121,
185,
249,
313,
377,
441,
505,
2,
66,
130,
194,
258,
322,
386,
450,
10,
74,
138,
202,
266,
330,
394,
458,
18,
82,
146,
210,
274,
338,
402,
466,
26,
90,
154,
218,
282,
346,
410,
474,
34,
98,
162,
226,
290,
354,
418,
482,
42,
106,
170,
234,
298,
362,
426,
490,
50,
114,
178,
242,
306,
370,
434,
498,
58,
122,
186,
250,
314,
378,
442,
506,
3,
67,
131,
195,
259,
323,
387,
451,
11,
75,
139,
203,
267,
331,
395,
459,
19,
83,
147,
211,
275,
339,
403,
467,
27,
91,
155,
219,
283,
347,
411,
475,
35,
99,
163,
227,
291,
355,
419,
483,
43,
107,
171,
235,
299,
363,
427,
491,
51,
115,
179,
243,
307,
371,
435,
499,
59,
123,
187,
251,
315,
379,
443,
507,
4,
68,
132,
196,
260,
324,
388,
452,
12,
76,
140,
204,
268,
332,
396,
460,
20,
84,
148,
212,
276,
340,
404,
468,
28,
92,
156,
220,
284,
348,
412,
476,
36,
100,
164,
228,
292,
356,
420,
484,
44,
108,
172,
236,
300,
364,
428,
492,
52,
116,
180,
244,
308,
372,
436,
500,
60,
124,
188,
252,
316,
380,
444,
508,
5,
69,
133,
197,
261,
325,
389,
453,
13,
77,
141,
205,
269,
333,
397,
461,
21,
85,
149,
213,
277,
341,
405,
469,
29,
93,
157,
221,
285,
349,
413,
477,
37,
101,
165,
229,
293,
357,
421,
485,
45,
109,
173,
237,
301,
365,
429,
493,
53,
117,
181,
245,
309,
373,
437,
501,
61,
125,
189,
253,
317,
381,
445,
509,
6,
70,
134,
198,
262,
326,
390,
454,
14,
78,
142,
206,
270,
334,
398,
462,
22,
86,
150,
214,
278,
342,
406,
470,
30,
94,
158,
222,
286,
350,
414,
478,
38,
102,
166,
230,
294,
358,
422,
486,
46,
110,
174,
238,
302,
366,
430,
494,
54,
118,
182,
246,
310,
374,
438,
502,
62,
126,
190,
254,
318,
382,
446,
510,
7,
71,
135,
199,
263,
327,
391,
455,
15,
79,
143,
207,
271,
335,
399,
463,
23,
87,
151,
215,
279,
343,
407,
471,
31,
95,
159,
223,
287,
351,
415,
479,
39,
103,
167,
231,
295,
359,
423,
487,
47,
111,
175,
239,
303,
367,
431,
495,
55,
119,
183,
247,
311,
375,
439,
503,
63,
127,
191,
255,
319,
383,
447,
511,
*/
};

#ifdef MIXED_RADIX
DATA_LOCATION short bit_rev_2_8_LUT[FFT_LEN_RADIX8] = {
    /*
0,
4,
2,
6,
1,
5,
3,
7,
32,
36,
34,
38,
33,
37,
35,
39,
16,
20,
18,
22,
17,
21,
19,
23,
48,
52,
50,
54,
49,
53,
51,
55,
8,
12,
10,
14,
9,
13,
11,
15,
40,
44,
42,
46,
41,
45,
43,
47,
24,
28,
26,
30,
25,
29,
27,
31,
56,
60,
58,
62,
57,
61,
59,
63,
256,
260,
258,
262,
257,
261,
259,
263,
288,
292,
290,
294,
289,
293,
291,
295,
272,
276,
274,
278,
273,
277,
275,
279,
304,
308,
306,
310,
305,
309,
307,
311,
264,
268,
266,
270,
265,
269,
267,
271,
296,
300,
298,
302,
297,
301,
299,
303,
280,
284,
282,
286,
281,
285,
283,
287,
312,
316,
314,
318,
313,
317,
315,
319,
128,
132,
130,
134,
129,
133,
131,
135,
160,
164,
162,
166,
161,
165,
163,
167,
144,
148,
146,
150,
145,
149,
147,
151,
176,
180,
178,
182,
177,
181,
179,
183,
136,
140,
138,
142,
137,
141,
139,
143,
168,
172,
170,
174,
169,
173,
171,
175,
152,
156,
154,
158,
153,
157,
155,
159,
184,
188,
186,
190,
185,
189,
187,
191,
384,
388,
386,
390,
385,
389,
387,
391,
416,
420,
418,
422,
417,
421,
419,
423,
400,
404,
402,
406,
401,
405,
403,
407,
432,
436,
434,
438,
433,
437,
435,
439,
392,
396,
394,
398,
393,
397,
395,
399,
424,
428,
426,
430,
425,
429,
427,
431,
408,
412,
410,
414,
409,
413,
411,
415,
440,
444,
442,
446,
441,
445,
443,
447,
64,
68,
66,
70,
65,
69,
67,
71,
96,
100,
98,
102,
97,
101,
99,
103,
80,
84,
82,
86,
81,
85,
83,
87,
112,
116,
114,
118,
113,
117,
115,
119,
72,
76,
74,
78,
73,
77,
75,
79,
104,
108,
106,
110,
105,
109,
107,
111,
88,
92,
90,
94,
89,
93,
91,
95,
120,
124,
122,
126,
121,
125,
123,
127,
320,
324,
322,
326,
321,
325,
323,
327,
352,
356,
354,
358,
353,
357,
355,
359,
336,
340,
338,
342,
337,
341,
339,
343,
368,
372,
370,
374,
369,
373,
371,
375,
328,
332,
330,
334,
329,
333,
331,
335,
360,
364,
362,
366,
361,
365,
363,
367,
344,
348,
346,
350,
345,
349,
347,
351,
376,
380,
378,
382,
377,
381,
379,
383,
192,
196,
194,
198,
193,
197,
195,
199,
224,
228,
226,
230,
225,
229,
227,
231,
208,
212,
210,
214,
209,
213,
211,
215,
240,
244,
242,
246,
241,
245,
243,
247,
200,
204,
202,
206,
201,
205,
203,
207,
232,
236,
234,
238,
233,
237,
235,
239,
216,
220,
218,
222,
217,
221,
219,
223,
248,
252,
250,
254,
249,
253,
251,
255,
448,
452,
450,
454,
449,
453,
451,
455,
480,
484,
482,
486,
481,
485,
483,
487,
464,
468,
466,
470,
465,
469,
467,
471,
496,
500,
498,
502,
497,
501,
499,
503,
456,
460,
458,
462,
457,
461,
459,
463,
488,
492,
490,
494,
489,
493,
491,
495,
472,
476,
474,
478,
473,
477,
475,
479,
504,
508,
506,
510,
505,
509,
507,
511
*/
};

#endif // MIXED_RADIX

#endif