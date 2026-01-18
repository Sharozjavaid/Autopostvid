#!/usr/bin/env python3
"""
Content Automations - Pre-written scripts for automated content generation

This module contains two automation types:
1. NARRATIVE VIDEOS: Machiavelli-themed videos with narration + moviepy transitions
2. STATIC SLIDESHOWS: Juicy "dangerous man" style slideshows for TikTok/Instagram

All scripts are pre-written with:
- Slide content (display text)
- Visual descriptions for image generation
- Proper formatting for the image style

Image Style: Dark, dramatic, Roman emperor aesthetic (oil painting, Caravaggio lighting)
"""

import os
import sys
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


# =============================================================================
# AUTOMATION 1: MACHIAVELLI NARRATIVE VIDEOS
# =============================================================================

MACHIAVELLI_SCRIPTS = [
    {
        "title": "Why Machiavelli Was Right About Human Nature",
        "topic": "Machiavelli's brutal truth about human nature",
        "content_type": "narrative_story",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "Machiavelli discovered something\nabout human nature\nthat made kings fear him.",
                "visual_description": "Dark Renaissance study, candlelit, a man in shadow writing at a wooden desk, quill pen in hand, dramatic Caravaggio lighting, oil painting style, burgundy and gold tones, ominous atmosphere"
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "display_text": "He watched Florence burn.\n\nHe saw friends betray each other\nfor a taste of power.",
                "visual_description": "Medieval Italian city at night, flames reflecting off stone buildings, silhouettes of men in conflict, dramatic chiaroscuro, Renaissance oil painting, smoke and fire, deep shadows"
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "display_text": "\"Men are ungrateful, fickle,\nliars and deceivers.\"\n\nHe wrote this from prison.",
                "visual_description": "Dark prison cell, iron bars, single shaft of light illuminating old parchment and chains, Renaissance dungeon aesthetic, oil painting texture, somber mood, aged stone walls"
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "display_text": "The Medici tortured him.\n\nHe still dedicated\nhis masterpiece to them.",
                "visual_description": "Ornate Renaissance throne room, powerful figure in shadow receiving a book, gold and crimson decor, Medici symbolism, dramatic lighting from tall windows, classical oil painting"
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "display_text": "Not out of love.\n\nBut because he understood:\n\nYou cannot fight reality.",
                "visual_description": "A lone philosopher figure standing before a massive chessboard with human-sized pieces, metaphor for political strategy, dark moody atmosphere, Renaissance setting, dramatic shadows"
            },
            {
                "slide_number": 6,
                "slide_type": "content",
                "display_text": "His lesson?\n\nSee people as they are.\n\nNot as you wish them to be.",
                "visual_description": "Close-up of eyes in shadow, reflecting candlelight, wise and calculating gaze, Renaissance portrait style, Rembrandt lighting, deep psychological intensity, oil painting texture"
            },
            {
                "slide_number": 7,
                "slide_type": "outro",
                "display_text": "The truth doesn't care\nabout your feelings.\n\nMachiavelli knew this\n500 years ago.",
                "visual_description": "Ancient book (The Prince) on a desk with a single candle burning low, smoke rising, symbolic ending, timeless wisdom, dark atmospheric, classical still life painting style"
            },
            {
                "slide_number": 8,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "The Prince: 5 Rules Machiavelli Taught About Power",
        "topic": "5 power lessons from Machiavelli's The Prince",
        "content_type": "list_educational",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "5 rules from Machiavelli\nthat powerful men\nstill use today.",
                "visual_description": "Imposing Renaissance prince on a throne, crown and scepter, dark red velvet robes, dramatic shadows, Caravaggio-style lighting, oil painting, power and authority emanating from the figure"
            },
            {
                "slide_number": 2,
                "slide_type": "list_item",
                "display_text": "1. It is better to be feared\nthan loved.\n\nFear is reliable.\nLove is not.",
                "visual_description": "A lion and a fox together in shadow, symbolizing strength and cunning, Renaissance allegorical painting, dramatic lighting, dark background, Machiavellian imagery"
            },
            {
                "slide_number": 3,
                "slide_type": "list_item",
                "display_text": "2. Never trust completely.\n\nEven your allies\nhave their own interests.",
                "visual_description": "Two Renaissance noblemen shaking hands while one hides a dagger behind his back, political intrigue, dark palace setting, suspicious atmosphere, oil painting style"
            },
            {
                "slide_number": 4,
                "slide_type": "list_item",
                "display_text": "3. Be a fox AND a lion.\n\nCunning to see traps.\nStrength to fight wolves.",
                "visual_description": "Split composition: half lion face, half fox face, merged together, powerful and cunning, Renaissance heraldic style, dramatic chiaroscuro, symbolic representation"
            },
            {
                "slide_number": 5,
                "slide_type": "list_item",
                "display_text": "4. Appear virtuous.\n\nBut be willing to act\nwhen virtue fails.",
                "visual_description": "Renaissance prince wearing two masks, one noble and one ruthless, theatrical imagery, Venetian masquerade influence, dramatic lighting, dual nature of power"
            },
            {
                "slide_number": 6,
                "slide_type": "list_item",
                "display_text": "5. Fortune favors the bold.\n\nHesitation is\nthe enemy of success.",
                "visual_description": "Fortune as a woman on a wheel, Renaissance allegory, a bold warrior reaching to seize opportunity, dynamic composition, classical mythology meets political philosophy"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "Machiavelli's Warning About Mercenaries",
        "topic": "Why Machiavelli said never trust hired men",
        "content_type": "narrative_story",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "\"Mercenaries are useless\nand dangerous.\"\n\nMachiavelli saw why.",
                "visual_description": "Group of medieval mercenary soldiers, armor and weapons, standing with crossed arms demanding payment, Italian Renaissance battlefield, oil painting, dramatic tension"
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "display_text": "They fight for money.\n\nWhen money runs out,\nso does their loyalty.",
                "visual_description": "Mercenary soldier counting gold coins while a battle rages behind him, split attention, greed versus duty, dark Renaissance scene, Caravaggio lighting"
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "display_text": "Italy was destroyed\nby hired armies.\n\nCity after city fell.",
                "visual_description": "Italian city-state burning and crumbling, soldiers in foreign armor marching through, defeat and destruction, dark historical scene, smoky atmosphere, oil painting"
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "display_text": "Machiavelli's solution?\n\nCitizen armies.\n\nMen who fight for home.",
                "visual_description": "Proud Florentine citizens in simple armor, standing unified before their city walls, determination and patriotism, Renaissance civic pride, warm lighting through clouds"
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "display_text": "The lesson for you:\n\nNever outsource\nwhat truly matters.",
                "visual_description": "Single figure standing alone, self-reliant, holding both sword and book, Renaissance humanist ideal, personal responsibility, dramatic solitary figure, oil painting"
            },
            {
                "slide_number": 6,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "How Machiavelli Lost Everything",
        "topic": "The tragic fall and redemption of Machiavelli",
        "content_type": "narrative_story",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "One day he was\nFlorence's top diplomat.\n\nThe next, he was nothing.",
                "visual_description": "Elegant Renaissance diplomat in fine robes, suddenly stripped of medals and position, dramatic before-and-after implied in single image, fall from grace, oil painting"
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "display_text": "The Medici returned.\n\nThey accused him of conspiracy.\n\nThey hung him by his arms.",
                "visual_description": "Dark torture chamber, man suspended by rope from ceiling, medieval interrogation, brutal Renaissance justice, extreme chiaroscuro, painful and raw, historical accuracy"
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "display_text": "Six drops of the rope.\n\nHis shoulders dislocated.\n\nHe never confessed.",
                "visual_description": "Close-up of anguished face in torchlight, sweat and determination, refusing to break, psychological portrait of endurance, Rembrandt-style lighting, intense emotion"
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "display_text": "Released but exiled.\n\nStripped of power.\n\nForgotten by the world.",
                "visual_description": "Solitary figure walking away from Florence on a dusty road, city walls behind him, lonely exile, autumn colors, melancholic atmosphere, Renaissance landscape"
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "display_text": "In exile,\nhe wrote The Prince.\n\nHis pain became wisdom.",
                "visual_description": "Small farmhouse study, humble but dignified, man writing by candlelight surrounded by books, creation of masterpiece in adversity, warm intimate scene, oil painting"
            },
            {
                "slide_number": 6,
                "slide_type": "outro",
                "display_text": "Sometimes you lose everything\nto find what matters.\n\nMachiavelli found truth.",
                "visual_description": "The Prince book illuminated by morning light, new beginning, hope emerging from darkness, symbolic rebirth of legacy, classical still life with meaning"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "Why Machiavelli Said Cruelty Can Be Mercy",
        "topic": "Machiavelli's dark wisdom on necessary cruelty",
        "content_type": "narrative_story",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "\"Cruelty well-used\nis more merciful\nthan kindness poorly applied.\"",
                "visual_description": "Renaissance judge in dark robes, weighing scales in one hand, sword in other, justice and severity, dramatic courtroom lighting, moral complexity, oil painting"
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "display_text": "Cesare Borgia conquered Romagna.\n\nIt was lawless chaos.\n\nMurder in the streets.",
                "visual_description": "Lawless medieval town, criminals running wild, violence in shadowy streets, before order was restored, chaotic and dangerous, dark Renaissance scene"
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "display_text": "He sent one man:\nRemirro de Orco.\n\nBrutal. Effective.",
                "visual_description": "Fearsome enforcer figure in black, imposing silhouette, bringing order through fear, executioner's presence, dark authority figure, Renaissance villain aesthetic"
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "display_text": "Peace was restored.\n\nBut the people hated Remirro.\n\nSo Borgia killed him publicly.",
                "visual_description": "Public execution in town square, crowd watching, political theater, body displayed as message, brutal Renaissance justice, symbolic sacrifice, dramatic scene"
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "display_text": "The people cheered.\n\nThey got order AND revenge.\n\nBorgia got loyalty.",
                "visual_description": "Crowd celebrating in town square, Renaissance festival atmosphere, ruler watching from balcony, masterful political manipulation, contrasting light and shadow"
            },
            {
                "slide_number": 6,
                "slide_type": "outro",
                "display_text": "The lesson:\n\nSwift severity prevents\nlingering suffering.\n\nThat is Machiavelli's mercy.",
                "visual_description": "Peaceful Italian town at sunset, order restored, calm after storm, the results of difficult decisions, golden hour lighting, hopeful conclusion, oil painting"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    }
]


# =============================================================================
# AUTOMATION 2: JUICY "DANGEROUS MAN" STATIC SLIDESHOWS
# =============================================================================

DANGEROUS_SLIDESHOW_SCRIPTS = [
    {
        "title": "5 Roman Emperors Who Were Actually Psychopaths",
        "topic": "Most insane Roman emperors in history",
        "content_type": "list_educational",
        "image_style": "classical",  # Oil painting, Caravaggio
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "Top 5 Roman Emperors\nWho Were Actually\nPsychopaths",
                "visual_description": "Imposing Roman emperor on golden throne, gladiator helmet with red plume, fur cloak over bare muscular torso, dark atmospheric throne room, Caravaggio oil painting style, dramatic chiaroscuro lighting, burgundy and gold tones, powerful and menacing presence"
            },
            {
                "slide_number": 2,
                "slide_type": "list_item",
                "display_text": "1. Caligula\n\nMade his horse a senator.\nDeclared himself a living god.\nKilled for entertainment.",
                "visual_description": "Mad emperor Caligula with wild eyes and golden laurel crown, ornate Roman robes, unstable expression, classical oil painting, dark palace background, unsettling charisma, Rembrandt lighting"
            },
            {
                "slide_number": 3,
                "slide_type": "list_item",
                "display_text": "2. Nero\n\nPlayed music while Rome burned.\nMurdered his own mother.\nBlamed Christians for the fire.",
                "visual_description": "Emperor Nero playing lyre with Rome burning in background, flames reflected in his eyes, twisted smile, dramatic classical painting, fire and destruction, infamous moment in history"
            },
            {
                "slide_number": 4,
                "slide_type": "list_item",
                "display_text": "3. Commodus\n\nFought as a gladiator.\nKilled exotic animals for sport.\nRuined the empire for fame.",
                "visual_description": "Emperor Commodus in gladiator armor in the Colosseum, muscular and vain, crowd in shadows behind, Russell Crowe Gladiator aesthetic, oil painting, dramatic arena lighting"
            },
            {
                "slide_number": 5,
                "slide_type": "list_item",
                "display_text": "4. Elagabalus\n\nBecame emperor at 14.\nHosted orgies in the palace.\nDead by 18.",
                "visual_description": "Young debauched Roman emperor surrounded by excess, rose petals falling, decadent throne room, classical painting of Roman excess, dark undertones beneath beauty"
            },
            {
                "slide_number": 6,
                "slide_type": "list_item",
                "display_text": "5. Caracalla\n\nMurdered his brother in his mother's arms.\nSlaughtered 20,000 Alexandrians.\nBuilt baths to seem kind.",
                "visual_description": "Brooding emperor Caracalla with intense gaze, military cloak, violent history in his eyes, Roman imperial portrait style, Caravaggio lighting, dangerous and calculating"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden Roman symbols and laurel wreaths, app store download aesthetic, premium mobile app promotion, classical philosophy touches"
            }
        ]
    },
    {
        "title": "5 Signs You're Becoming Dangerous",
        "topic": "Signs of developing personal power",
        "content_type": "wisdom_slideshow",
        "image_style": "cinematic",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "5 Signs You're Becoming\nDangerous",
                "visual_description": "Mysterious man in shadow, only eyes visible, dark suit, powerful presence, cinematic lighting, movie poster aesthetic, teal and orange color grading, dangerous and compelling"
            },
            {
                "slide_number": 2,
                "slide_type": "insight",
                "display_text": "1. You stopped explaining yourself.\n\nWeak people justify.\nStrong people act.",
                "visual_description": "Confident man walking away from group of people talking, back turned, unbothered, cinematic wide shot, urban setting, lone wolf energy, film noir lighting"
            },
            {
                "slide_number": 3,
                "slide_type": "insight",
                "display_text": "2. Silence became your weapon.\n\nYou learned that words\nare often wasted.",
                "visual_description": "Man in suit, calm expression, seated while chaos happens around him, unphased, strategic silence, cinematic close-up, powerful stillness, dark tones"
            },
            {
                "slide_number": 4,
                "slide_type": "insight",
                "display_text": "3. You cut people off without guilt.\n\nLoyalty is earned.\nNot given freely.",
                "visual_description": "Man walking through door, closing it behind him, leaving old life, decisive action, cinematic framing, dramatic backlighting, moving forward alone"
            },
            {
                "slide_number": 5,
                "slide_type": "insight",
                "display_text": "4. You became comfortable alone.\n\nSolitude is where\npower is forged.",
                "visual_description": "Solitary figure on rooftop overlooking city at night, contemplative, powerful isolation, cinematic cityscape, moody atmosphere, self-reliance embodied"
            },
            {
                "slide_number": 6,
                "slide_type": "insight",
                "display_text": "5. You stopped fearing loss.\n\nBecause you know\nyou can rebuild from nothing.",
                "visual_description": "Man standing before destroyed building, ready to rebuild, phoenix energy, resilience, cinematic wide shot, dawn breaking, hopeful yet dangerous determination"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "4 Truths About Power Nobody Tells You",
        "topic": "Dark truths about power and influence",
        "content_type": "wisdom_slideshow",
        "image_style": "classical",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "4 Truths About Power\nNobody Tells You",
                "visual_description": "Shadowy king on iron throne, crown in shadow, hands gripping armrests, dark medieval chamber, Caravaggio lighting, oil painting, power and isolation"
            },
            {
                "slide_number": 2,
                "slide_type": "insight",
                "display_text": "1. Power reveals who you really are.\n\nIt doesn't corrupt.\nIt exposes.",
                "visual_description": "Two-faced Renaissance portrait, light and dark sides, moral duality, classical painting technique, split lighting, psychological depth"
            },
            {
                "slide_number": 3,
                "slide_type": "insight",
                "display_text": "2. The powerful are always alone.\n\nEvery crown comes\nwith invisible walls.",
                "visual_description": "Lonely king at massive banquet table, empty chairs all around, isolation of leadership, dark grand hall, oil painting, melancholic power"
            },
            {
                "slide_number": 4,
                "slide_type": "insight",
                "display_text": "3. Most people want to be led.\n\nThey crave certainty\nmore than freedom.",
                "visual_description": "Crowd of people looking up at single figure on balcony, Renaissance political scene, masses and leader dynamic, dramatic perspective, oil painting"
            },
            {
                "slide_number": 5,
                "slide_type": "insight",
                "display_text": "4. Power is responsibility.\n\nEvery decision echoes.\nEvery mistake costs lives.",
                "visual_description": "Ruler's hands signing document by candlelight, weight of decision, quill pen and wax seal, Renaissance administrative scene, heavy atmosphere, classical painting"
            },
            {
                "slide_number": 6,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "Why Weak Men Create Hard Times",
        "topic": "The cycle of strong and weak men",
        "content_type": "wisdom_slideshow",
        "image_style": "classical",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "Why Weak Men\nCreate Hard Times",
                "visual_description": "Crumbling Roman empire scene, weak emperor on throne while barbarians approach, decline of civilization, dramatic oil painting, Caravaggio lighting, historical decay"
            },
            {
                "slide_number": 2,
                "slide_type": "content",
                "display_text": "Hard times create strong men.\n\nStruggle forges character.\nPain builds resilience.",
                "visual_description": "Spartan warriors training, sweat and determination, harsh conditions creating strength, classical Greek military training, oil painting, golden morning light through dust"
            },
            {
                "slide_number": 3,
                "slide_type": "content",
                "display_text": "Strong men create good times.\n\nThey build.\nThey protect.\nThey sacrifice.",
                "visual_description": "Roman builders constructing aqueduct, civilization at its height, strong men working together, prosperity and achievement, Renaissance painting of Roman glory"
            },
            {
                "slide_number": 4,
                "slide_type": "content",
                "display_text": "Good times create weak men.\n\nComfort breeds complacency.\nEase kills ambition.",
                "visual_description": "Decadent Roman feast, lazy nobles reclining, excess and softness, decline beginning, classical painting of Roman decadence, warning signs of fall"
            },
            {
                "slide_number": 5,
                "slide_type": "content",
                "display_text": "Weak men create hard times.\n\nAnd the cycle repeats.\n\nWhere are you in it?",
                "visual_description": "Circular composition showing all four stages, wheel of fortune concept, Renaissance allegorical painting, cycle of history, powerful visual metaphor"
            },
            {
                "slide_number": 6,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "5 Philosophers Who Were Actually Dangerous",
        "topic": "Philosophers who lived dangerously",
        "content_type": "list_educational",
        "image_style": "classical",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "5 Philosophers\nWho Were Actually\nDangerous",
                "visual_description": "Group of shadowy philosopher figures, ominous gathering, candles illuminating faces, secret society aesthetic, Renaissance conspiracy, oil painting, dangerous intellectuals"
            },
            {
                "slide_number": 2,
                "slide_type": "list_item",
                "display_text": "1. Socrates\n\nCorrupted the youth.\nQuestioned everything.\nChose death over silence.",
                "visual_description": "Socrates drinking hemlock, surrounded by weeping students, defiant expression, classical Greek scene, dramatic moment of martyrdom, oil painting, ultimate sacrifice for truth"
            },
            {
                "slide_number": 3,
                "slide_type": "list_item",
                "display_text": "2. Machiavelli\n\nSurvived torture.\nExposed how power really works.\nStill feared 500 years later.",
                "visual_description": "Machiavelli in shadows writing The Prince, scheming expression, Renaissance study, political dangerous, classical portrait, calculating intelligence"
            },
            {
                "slide_number": 4,
                "slide_type": "list_item",
                "display_text": "3. Nietzsche\n\nDeclared God dead.\nPredicted world wars.\nDrove himself mad with truth.",
                "visual_description": "Nietzsche with intense piercing gaze, wild mustache, abyss reflected in eyes, German philosopher, dark psychological portrait, edge of madness and genius"
            },
            {
                "slide_number": 5,
                "slide_type": "list_item",
                "display_text": "4. Diogenes\n\nLived in a barrel.\nMocked Alexander the Great.\nCalled everyone a fool.",
                "visual_description": "Diogenes with lantern in daylight searching for honest man, cynical expression, ragged philosopher, ancient Greek marketplace, confrontational wisdom, oil painting"
            },
            {
                "slide_number": 6,
                "slide_type": "list_item",
                "display_text": "5. Seneca\n\nAdvised a tyrant.\nBecame richest man in Rome.\nForced to kill himself.",
                "visual_description": "Seneca calmly cutting his wrists in bath, stoic acceptance of death, Roman villa setting, tragic dignity, classical painting of stoic death, controlled ending"
            },
            {
                "slide_number": 7,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    },
    {
        "title": "What Stoics Knew About Enemies",
        "topic": "Stoic wisdom on dealing with enemies",
        "content_type": "wisdom_slideshow",
        "image_style": "classical",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "hook",
                "display_text": "What The Stoics Knew\nAbout Enemies",
                "visual_description": "Roman general Marcus Aurelius in military tent, studying philosophy scrolls while army camps outside, warrior philosopher, oil painting, Caravaggio lighting, wisdom and war"
            },
            {
                "slide_number": 2,
                "slide_type": "insight",
                "display_text": "1. Your enemies reveal your weaknesses.\n\nThey attack where you're soft.\nThank them for the map.",
                "visual_description": "Spartan looking at reflection in shield, seeing own flaws, self-examination through conflict, classical Greek warrior, introspective moment, oil painting"
            },
            {
                "slide_number": 3,
                "slide_type": "insight",
                "display_text": "2. Anger gives them power over you.\n\nStay calm.\nThink clearly.\nStrike precisely.",
                "visual_description": "Stoic Roman senator remaining calm while others argue angrily in Senate, controlled power, classical Roman political scene, composure amid chaos"
            },
            {
                "slide_number": 4,
                "slide_type": "insight",
                "display_text": "3. The best revenge is living well.\n\nYour success is\ntheir defeat.",
                "visual_description": "Prosperous Roman villa, former enemy watching from outside gates, living well as victory, contrast of fortune, classical painting, ironic justice"
            },
            {
                "slide_number": 5,
                "slide_type": "insight",
                "display_text": "4. Some enemies become allies.\n\nTime changes everything.\nDon't burn bridges forever.",
                "visual_description": "Two former enemies now shaking hands, Roman political alliance, pragmatic peace, Renaissance diplomatic scene, mature reconciliation, oil painting"
            },
            {
                "slide_number": 6,
                "slide_type": "cta",
                "display_text": "Want to learn philosophy in practice?\n\nDownload PhilosophizeMe\non the App Store. It's free.",
                "visual_description": "Elegant dark background with subtle golden philosophical symbols, app store download aesthetic, premium mobile app promotion, clean and modern with classical philosophy touches"
            }
        ]
    }
]


# =============================================================================
# RUNNER FUNCTIONS
# =============================================================================

class ContentAutomationRunner:
    """
    Runs pre-written content automations for narrative videos and static slideshows.
    """
    
    def __init__(self):
        self.output_dir = Path("generated_slideshows")
        self.video_output_dir = Path("generated_videos")
        self.output_dir.mkdir(exist_ok=True)
        self.video_output_dir.mkdir(exist_ok=True)
        
        # Track what's been generated
        self.generated_today = []
    
    def get_next_machiavelli_script(self) -> Dict:
        """Get the next Machiavelli script to generate."""
        # Simple round-robin based on what hasn't been done recently
        return random.choice(MACHIAVELLI_SCRIPTS)
    
    def get_next_dangerous_script(self) -> Dict:
        """Get the next 'dangerous' slideshow script to generate."""
        return random.choice(DANGEROUS_SLIDESHOW_SCRIPTS)
    
    def generate_narrative_video(self, script: Dict) -> Dict:
        """
        Generate a narrative video with:
        1. AI-generated images for each slide
        2. ElevenLabs narration
        3. MoviePy transitions (crossfade)
        4. Final assembled video
        """
        from backend.app.services.gpt_image_generator import GPTImageGenerator
        from backend.app.services.text_overlay import TextOverlay
        from backend.app.services.voice_generator import VoiceGenerator
        from backend.app.services.video_assembler import VideoAssembler
        
        title = script['title']
        slides = script['slides']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        project_dir = self.output_dir / f"{safe_title}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎬 GENERATING NARRATIVE VIDEO: {title}")
        print(f"   📁 Output: {project_dir}")
        print(f"   🎴 Slides: {len(slides)}")
        
        # Step 1: Generate background images
        print("\n1️⃣  Generating background images...")
        image_gen = GPTImageGenerator(quality="low")
        text_overlay = TextOverlay(fonts_dir="fonts", default_style="modern")
        
        background_paths = []
        final_image_paths = []
        
        for i, slide in enumerate(slides):
            print(f"   🖼️  Slide {i+1}/{len(slides)}: Generating background...")
            
            bg_path = image_gen.generate_background(
                visual_description=slide['visual_description'],
                scene_number=i + 1,
                story_title=safe_title
            )
            
            if bg_path:
                background_paths.append(bg_path)
                
                # Apply text overlay
                output_path = str(project_dir / f"slide_{i}.png")
                
                if slide['slide_type'] in ['hook', 'cta']:
                    text_overlay.create_hook_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        hook_text=slide['display_text'],
                        font_name="social",
                        style="modern"
                    )
                else:
                    text_overlay.create_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        title=slide['display_text'],
                        subtitle="",
                        slide_number=None,
                        font_name="social",
                        style="modern"
                    )
                
                final_image_paths.append(output_path)
                print(f"   ✅ Slide {i+1} complete")
            else:
                print(f"   ❌ Slide {i+1} failed")
        
        # Step 2: Generate narration
        print("\n2️⃣  Generating voice narration...")
        voice_gen = VoiceGenerator()
        
        # Build full narration text
        narration_text = ""
        scenes_for_timing = []
        for slide in slides:
            # Clean text for narration (remove line breaks)
            clean_text = slide['display_text'].replace('\n', ' ').strip()
            narration_text += clean_text + " "
            scenes_for_timing.append({
                "scene_number": slide['slide_number'],
                "text": clean_text
            })
        
        audio_result = voice_gen.generate_voiceover_with_timestamps(
            script=narration_text.strip(),
            scenes=scenes_for_timing,
            filename=f"{safe_title}_narration.mp3"
        )
        
        if not audio_result:
            print("   ❌ Narration failed, trying simple generation...")
            audio_path = voice_gen.generate_voiceover(
                narration_text.strip(),
                filename=f"{safe_title}_narration.mp3"
            )
        else:
            audio_path = audio_result['audio_path']
            print(f"   ✅ Narration: {audio_result.get('total_duration', 0):.1f}s")
        
        # Step 3: Assemble video with transitions
        print("\n3️⃣  Assembling video with crossfade transitions...")
        assembler = VideoAssembler()
        
        video_path = assembler.create_philosophy_video(
            scenes=scenes_for_timing,
            audio_path=audio_path,
            image_paths=final_image_paths,
            story_title=safe_title,
            transition="crossfade",
            transition_duration=0.3
        )
        
        if video_path:
            print(f"\n✅ VIDEO COMPLETE: {video_path}")
        else:
            print("\n❌ Video assembly failed")
        
        # Save metadata
        result = {
            "success": video_path is not None,
            "title": title,
            "video_path": video_path,
            "audio_path": audio_path,
            "image_paths": final_image_paths,
            "slide_count": len(slides),
            "project_dir": str(project_dir),
            "timestamp": timestamp
        }
        
        with open(project_dir / "metadata.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        return result
    
    def generate_static_slideshow(self, script: Dict) -> Dict:
        """
        Generate a static slideshow (images only) for TikTok/Instagram.
        
        1. AI-generated images for each slide
        2. Text overlay burned in
        3. Ready for photo carousel posting
        """
        from backend.app.services.gpt_image_generator import GPTImageGenerator
        from backend.app.services.text_overlay import TextOverlay
        
        title = script['title']
        slides = script['slides']
        image_style = script.get('image_style', 'classical')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]
        project_dir = self.output_dir / f"{safe_title}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎴 GENERATING STATIC SLIDESHOW: {title}")
        print(f"   📁 Output: {project_dir}")
        print(f"   🎴 Slides: {len(slides)}")
        print(f"   🎨 Style: {image_style}")
        
        # Generate images
        image_gen = GPTImageGenerator(quality="low")
        text_overlay = TextOverlay(fonts_dir="fonts", default_style="modern")
        
        final_image_paths = []
        
        for i, slide in enumerate(slides):
            print(f"   🖼️  Slide {i+1}/{len(slides)}: Generating...")
            
            bg_path = image_gen.generate_background(
                visual_description=slide['visual_description'],
                scene_number=i + 1,
                story_title=safe_title
            )
            
            if bg_path:
                output_path = str(project_dir / f"slide_{i}.png")
                
                if slide['slide_type'] in ['hook', 'cta']:
                    text_overlay.create_hook_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        hook_text=slide['display_text'],
                        font_name="social",
                        style="modern"
                    )
                else:
                    text_overlay.create_slide(
                        background_path=bg_path,
                        output_path=output_path,
                        title=slide['display_text'],
                        subtitle="",
                        slide_number=None,
                        font_name="social",
                        style="modern"
                    )
                
                final_image_paths.append(output_path)
                print(f"   ✅ Slide {i+1} complete")
            else:
                print(f"   ❌ Slide {i+1} failed")
        
        print(f"\n✅ SLIDESHOW COMPLETE: {len(final_image_paths)} slides")
        
        result = {
            "success": len(final_image_paths) > 0,
            "title": title,
            "image_paths": final_image_paths,
            "slide_count": len(slides),
            "project_dir": str(project_dir),
            "timestamp": timestamp,
            "image_style": image_style
        }
        
        with open(project_dir / "metadata.json", "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        return result
    
    def post_to_social(self, result: Dict, post_tiktok: bool = True, post_instagram: bool = True) -> Dict:
        """Post generated content to TikTok and Instagram."""
        from backend.app.services.tiktok_poster import TikTokPoster
        from backend.app.services.instagram_poster import InstagramPoster
        
        image_paths = result.get('image_paths', [])
        title = result.get('title', 'Philosophy Content')
        video_path = result.get('video_path')
        
        post_results = {
            "tiktok": None,
            "instagram": None
        }
        
        # Generate caption
        caption = f"{title}\n\n#philosophy #stoicism #wisdom #motivation #mindset #ancientwisdom #machiavelli #power"
        
        if post_tiktok:
            print("\n📱 Posting to TikTok...")
            try:
                tiktok = TikTokPoster()
                
                if video_path:
                    # Post video
                    tiktok_result = tiktok.upload_video(video_path, caption)
                else:
                    # Post photo slideshow
                    tiktok_result = tiktok.post_photo_slideshow(image_paths, caption)
                
                post_results["tiktok"] = tiktok_result
                if tiktok_result.get("success"):
                    print(f"   ✅ TikTok: Posted to drafts")
                else:
                    print(f"   ❌ TikTok: {tiktok_result.get('error')}")
            except Exception as e:
                print(f"   ❌ TikTok error: {e}")
                post_results["tiktok"] = {"success": False, "error": str(e)}
        
        if post_instagram:
            print("\n📸 Posting to Instagram...")
            try:
                instagram = InstagramPoster()
                
                if video_path:
                    # Instagram doesn't support video via Post Bridge currently
                    print("   ⚠️ Video posting to Instagram not supported, posting images only")
                    ig_result = instagram.post_carousel(image_paths, caption)
                else:
                    ig_result = instagram.post_carousel(image_paths, caption)
                
                post_results["instagram"] = ig_result
                if ig_result.get("success"):
                    print(f"   ✅ Instagram: Posted!")
                else:
                    print(f"   ❌ Instagram: {ig_result.get('error')}")
            except Exception as e:
                print(f"   ❌ Instagram error: {e}")
                post_results["instagram"] = {"success": False, "error": str(e)}
        
        return post_results


def run_machiavelli_narrative():
    """Run one Machiavelli narrative video generation."""
    runner = ContentAutomationRunner()
    script = runner.get_next_machiavelli_script()
    result = runner.generate_narrative_video(script)
    
    if result.get("success"):
        post_results = runner.post_to_social(result, post_tiktok=True, post_instagram=True)
        result["social_posts"] = post_results
    
    return result


def run_dangerous_slideshow():
    """Run one 'dangerous' static slideshow generation."""
    runner = ContentAutomationRunner()
    script = runner.get_next_dangerous_script()
    result = runner.generate_static_slideshow(script)
    
    if result.get("success"):
        post_results = runner.post_to_social(result, post_tiktok=True, post_instagram=True)
        result["social_posts"] = post_results
    
    return result


def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Content Automations Runner")
    parser.add_argument("--type", choices=["narrative", "slideshow", "both"], default="both")
    parser.add_argument("--no-post", action="store_true", help="Skip social media posting")
    parser.add_argument("--list", action="store_true", help="List available scripts")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n=== MACHIAVELLI NARRATIVE SCRIPTS ===")
        for i, s in enumerate(MACHIAVELLI_SCRIPTS):
            print(f"{i+1}. {s['title']}")
        
        print("\n=== DANGEROUS SLIDESHOW SCRIPTS ===")
        for i, s in enumerate(DANGEROUS_SLIDESHOW_SCRIPTS):
            print(f"{i+1}. {s['title']}")
        return
    
    runner = ContentAutomationRunner()
    
    if args.type in ["narrative", "both"]:
        print("\n" + "="*60)
        print("RUNNING MACHIAVELLI NARRATIVE VIDEO")
        print("="*60)
        
        script = runner.get_next_machiavelli_script()
        result = runner.generate_narrative_video(script)
        
        if result.get("success") and not args.no_post:
            runner.post_to_social(result)
    
    if args.type in ["slideshow", "both"]:
        print("\n" + "="*60)
        print("RUNNING DANGEROUS SLIDESHOW")
        print("="*60)
        
        script = runner.get_next_dangerous_script()
        result = runner.generate_static_slideshow(script)
        
        if result.get("success") and not args.no_post:
            runner.post_to_social(result)


if __name__ == "__main__":
    main()
