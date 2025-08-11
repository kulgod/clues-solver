from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum 

from src.python.game_state import Suspect, Label

"""How to play Clues by Sam

Your goal is to figure out who is criminal and who is innocent.
Based on what you know, tap on a suspect to choose if they are innocent or criminal. They might reveal a new hint.
You cannot guess! Just like in real life, you can't convict someone based on a 50/50 hunch. There is always a logical next choice, even when you think there isn't!

Clarifying details

Everyone is either a criminal or innocent.

Professions don't make some innocent or criminal, unless a hint suggest so. A police is as criminal as an accountant until proven otherwise.
Everyone speaks the truth, even the criminals.

"Neighbors" always include diagonal neigbors. One person can have up to 8 neighbors.

"In between" (or sometimes just "between") means the persons between the two, not including the two.

"Connected" means a chain of orthogonal adjacency. For example "all criminals in row 1 are connected" means there are no innocents between any two criminals in that row.
Rows go sideways and are numbered 1,2,3,4,5. Columns go up and down and lettered A,B,C,D.

"To the left/right" always means somewhere in the same row. Above/below always means somewhere in the same column.

"Directly to the left/right/above/below" always means the neighbor to the left/right/above/below.

"All" always means there's at least one. It doesn't necessarily mean there's more than one.

"Any" doesn't tell anything about the number of criminals/innocents. "Any criminal on row 2 is..." means "If there are any criminals on row 2, they would be ..."

"One of" the innocents/criminals / one of several / one of multiple always means there's at least two innocents/criminals. This is slightly conflicting with "All innocents/criminals..." and I'm open for suggestions how to improve the phrasing here!
Common neighbors means those who are neighbors of both persons. It does not include the persons themselves.

"In total" always means the sum of all in the group(s). Two criminal cops and cooks in total means there might be 1 cop and 1 cook, or 0 cops and 2 cooks, or 2 cops and 0 cooks.

"Corner" means the four corners.

"Edge" means the 14 persons "surrounding" the board, including corners.

... "the most" always means uniquely the most. If John has the most criminal neighbors, no one can have as many criminal neighbors as John.

An even number means numbers divisible by two: 0, 2, 4, 6... and an odd number means everything else: 1, 3, 5, 7...

You never need to guess. In fact, the game only allows you to make logical choices.
"""

example_board_2025_08_09 = [
    [
        Suspect.unknown(
            "Adam", 
            "judge", 
            "Wasn't a judge throwing wooden hammers on Thursday?"
        ),
        Suspect.unknown(
            "Bruce", 
            "judge", 
            "There's an equal number of criminals in columns B and D"
        ),
        Suspect.unknown(
            "Carl", 
            "cop", 
            "The only criminal below Ollie is Ollie's neighbor"
        ),
        Suspect.unknown(
            "Daniel", 
            "judge", 
            "Column C has more innocents than any other column"
        ),
    ],
    [
        Suspect.unknown(
            "Emily", 
            "coder", 
            "I'm good at throwing CDs. Makes me feel like a cyber ninja!"
        ),
        Suspect.unknown(
            "Floyd", 
            "mech", 
            "Mind if I throw a wrench into your deductive work?"
        ),
        Suspect.unknown(
            "Isaac", 
            "coder", 
            "I've heard of server throwing competitions. What a waste!"
        ),
        Suspect.unknown(
            "Karen", 
            "coder", 
            "Both innocents above Wanda are Isaac's neighbors"
        ),
    ],
    [
        Suspect.unknown(
            "Laura", 
            "guard", 
            "Are you throwing me into jail?"
        ),
        Suspect.unknown(
            "Mary", 
            "painter", 
            "Bruce has more criminal neighbors than Vicky"
        ),
        # Starting point
        Suspect.innocent( 
            "Nancy", 
            "cop", 
            "Tyler is one of 2 criminals below Karen",
        ),
        Suspect.unknown(
            "Ollie", 
            "painter", 
            "There are as many criminals as innocents in between Bruce and Rob"
        ),
    ],
    [
        Suspect.unknown(
            "Pam", 
            "sleuth", 
            "All innocents below Carl are connected"
        ),
        Suspect.unknown(
            "Rob", 
            "guard", 
            "Bruce has exactly 2 innocent neighbors"
        ),
        Suspect.unknown(
            "Susan", 
            "mech", 
            "There are 11 innocents in total"
        ),
        Suspect.unknown(
            "Tyler", 
            "mech", 
            "There is one innocent cop above Susan"
        ),
    ],
    [
        Suspect.unknown(
            "Vicky", 
            "doctor", 
            "No more throwing tools, please! Someone might get hurt!"
        ),
        Suspect.unknown(
            "Wanda",
            "cop", 
            "Both criminals to the left of Karen are connected"
        ),
        Suspect.unknown(
            "Xavi", 
            "sleuth", 
            "All innocents in row 3 are neighboring Isaac"
        ),
        Suspect.unknown(
            "Zena", 
            "doctor", 
            "The only innocent above me is closer to Floyd than to Bruce"
        ),
    ]
]