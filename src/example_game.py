from typing import List, Tuple
from dataclasses import dataclass
from enum import Enum 



@dataclass
class Suspect:
    name: str
    occupation: str
    hint: str 


@dataclass 
class ExampleGame:
    board: List[List[Suspect]]
    starting_point = Tuple[int] # (x, y) coordinate


example_2025_08_09 = [
    [
        Suspect(
            "Adam", 
            "judge", 
            "Wasn't a judge throwing wooden hammers on Thursday?"
        ),
        Suspect(
            "Bruce", 
            "judge", 
            "There's an equal number of criminals in columns B and D"
        ),
        Suspect(
            "Carl", 
            "cop", 
            "The only criminal below Ollie is Ollie's neighbor"
        ),
        Suspect(
            "Daniel", 
            "judge", 
            "Column C has more innocents than any other column"
        ),
    ],
    [
        Suspect(
            "Emily", 
            "coder", 
            "I'm good at throwing CDs. Makes me feel like a cyber ninja!"
        ),
        Suspect(
            "Floyd", 
            "mech", 
            "Mind if I throw a wrench into your deductive work?"
        ),
        Suspect(
            "Isaac", 
            "coder", 
            "I've heard of server throwing competitions. What a waste!"
        ),
        Suspect(
            "Karen", 
            "coder", 
            "Both innocents above Wanda are Isaac's neighbors"
        ),
    ],
    [
        Suspect(
            "Laura", 
            "guard", 
            "Are you throwing me into jail?"
        ),
        Suspect(
            "Mary", 
            "painter", 
            "Bruce has more criminal neighbors than Vicky"
        ),
        Suspect( ## Starting point
            "Nancy", 
            "cop", 
            "Tyler is one of 2 criminals below Karen"
        ),
        Suspect(
            "Ollie", 
            "painter", 
            "There are as many criminals as innocents in between Bruce and Rob"
        ),
    ],
    [
        Suspect(
            "Pam", 
            "sleuth", 
            "All innocents below Carl are connected"
        ),
        Suspect(
            "Rob", 
            "guard", 
            "Bruce has exactly 2 innocent neighbors"
        ),
        Suspect(
            "Susan", 
            "mech", 
            "There are 11 innocents in total"
        ),
        Suspect(
            "Tyler", 
            "mech", 
            "There is one innocent cop above Susan"
        ),
    ],
    [
        Suspect(
            "Vicky", 
            "doctor", 
            "No more throwing tools, please! Someone might get hurt!"
        ),
        Suspect(
            "Wanda",
            "cop", 
            "Both criminals to the left of Karen are connected"
        ),
        Suspect(
            "Xavi", 
            "sleuth", 
            "All innocents in row 3 are neighboring Isaac"
        ),
        Suspect(
            "Zena", 
            "doctor", 
            "The only innocent above me is closer to Floyd than to Bruce"
        ),
    ]
]