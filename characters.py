"""
characters.py
Base characters database for "Who am I?" game
Contains 30+ real and fictional personalities
"""

from dataclasses import dataclass
from typing import List, Dict
import random

@dataclass
class Character:
    """Character card data structure"""
    name: str
    category: str
    hints: List[str]

# Characters database
CHARACTERS: List[Character] = [
    # Ancient World & Medieval
    Character("Alexander the Great", "Ancient", [
        "Macedonian conqueror", "Student of Aristotle", "Conquered Persia", "Died at 32", "Hellenistic empire"
    ]),
    Character("Julius Caesar", "Ancient", [
        "Roman dictator", "Crossed Rubicon", "Veni vidi vici", "Assassinated by senators", "Gallic Wars"
    ]),
    Character("Cleopatra", "Ancient", [
        "Egyptian queen", "Ptolemaic dynasty", "Mark Antony relationship", "Last pharaoh", "Died by asp bite"
    ]),
    Character("Genghis Khan", "Medieval", [
        "Mongol emperor", "United Mongol tribes", "Largest empire", "Yuan dynasty founder", "Horse archer tactics"
    ]),
    Character("Joan of Arc", "Medieval", [
        "French heroine", "Maid of Orleans", "Hundred Years War", "Burned at stake", "Saint of France"
    ]),
    Character("Leonardo da Vinci", "Renaissance", [
        "Renaissance polymath", "Mona Lisa painter", "Italian", "Inventor", "Last Supper"
    ]),
    Character("Christopher Columbus", "Renaissance", [
        "Italian explorer", "Discovered America", "Spanish ships", "Westward route", "Three voyages"
    ]),
    
    # Rulers & Politicians
    Character("Napoleon Bonaparte", "Politics", [
        "French emperor", "Military genius", "Waterloo battle", "Exiled to Elba", "Short stature"
    ]),
    Character("Catherine the Great", "Politics", [
        "Russian empress", "Enlightened despot", "Expanded Russia", "German-born", "Cultural patron"
    ]),
    Character("Peter the Great", "Politics", [
        "Russian tsar", "Westernized Russia", "St. Petersburg founder", "Tall stature", "Modernizer"
    ]),
    Character("Abraham Lincoln", "Politics", [
        "US President", "Emancipation Proclamation", "Assassinated in theater", "Civil War leader", "Tall hat"
    ]),
    Character("Winston Churchill", "Politics", [
        "British Prime Minister", "WWII leader", "Nobel Prize in Literature", "Cigar smoker", "Iron Curtain speech"
    ]),
    Character("Mahatma Gandhi", "Politics", [
        "Indian independence leader", "Non-violent protest", "Salt March", "Nobel Peace Prize nominee", "Dhoti wearer"
    ]),
    Character("Nelson Mandela", "Politics", [
        "South African president", "Anti-apartheid leader", "27 years imprisoned", "Nobel Peace Prize", "Rainbow nation"
    ]),
    
    # Scientists & Inventors
    Character("Albert Einstein", "Science", [
        "Famous physicist", "E=mc²", "Nobel Prize winner", "German-born", "Theory of relativity"
    ]),
    Character("Isaac Newton", "Science", [
        "English physicist", "Gravity laws", "Three laws of motion", "Apple story", "Calculus co-inventor"
    ]),
    Character("Nikola Tesla", "Science", [
        "Serbian inventor", "Alternating current", "Tesla coil", "Wireless pioneer", "Edison rival"
    ]),
    Character("Marie Curie", "Science", [
        "Physicist and chemist", "Two Nobel Prizes", "Polish-born", "Radioactivity research", "First woman Nobel laureate"
    ]),
    Character("Charles Darwin", "Science", [
        "English naturalist", "Evolution theory", "Natural selection", "Galapagos Islands", "Origin of Species"
    ]),
    Character("Galileo Galilei", "Science", [
        "Italian astronomer", "Telescope improvements", "Heliocentric model", "Inquisition trial", "Pendulum studies"
    ]),
    
    # Cultural Figures
    Character("William Shakespeare", "Culture", [
        "English playwright", "Romeo and Juliet", "Globe Theatre", "16th-17th century", "Sonnets"
    ]),
    Character("Ludwig van Beethoven", "Culture", [
        "German composer", "9th Symphony", "Deaf composer", "Moonlight Sonata", "Classical to Romantic"
    ]),
    Character("Vincent van Gogh", "Culture", [
        "Dutch painter", "Starry Night", "Sunflowers", "Cut off ear", "Post-Impressionist"
    ]),
    Character("Mozart", "Culture", [
        "Austrian composer", "Child prodigy", "Requiem", "Magic Flute", "Classical period"
    ]),
    Character("Pablo Picasso", "Culture", [
        "Spanish painter", "Cubism founder", "Guernica", "Blue Period", "Modern art"
    ]),
    
    # Military Leaders
    Character("Napoleon", "Military", [
        "French emperor", "Military genius", "Waterloo battle", "Exiled to Elba", "Short stature"
    ]),
    Character("Alexander Suvorov", "Military", [
        "Russian general", "Never lost battle", "Swiss campaign", "Alps crossing", "Hard training"
    ]),
    Character("Georgy Zhukov", "Military", [
        "Soviet marshal", "WWII hero", "Stalingrad defense", "Berlin capture", "Four times Hero"
    ]),
    Character("Hannibal", "Military", [
        "Carthaginian general", "Crossed Alps with elephants", "Punic Wars", "Cannae battle", "Rome's enemy"
    ]),
    Character("Queen Elizabeth II", "Politics", [
        "British monarch", "Longest reign", "Wore colorful outfits", "Corgis lover", "Windsor dynasty"
    ]),
    
    # Fictional characters
    Character("Sherlock Holmes", "Fiction", [
        "Detective", "221B Baker Street", "Dr. Watson friend", "Violin player", "Elementary deduction"
    ]),
    Character("Harry Potter", "Fiction", [
        "Wizard", "Hogwarts student", "Lightning scar", "Gryffindor house", "Defeated Voldemort"
    ]),
    Character("Hermione Granger", "Fiction", [
        "Witch", "Hogwarts student", "Brilliant student", "Gryffindor house", "Time-turner user"
    ]),
    Character("Darth Vader", "Fiction", [
        "Star Wars villain", "Dark side", "Black armor", "Luke's father", "Lightsaber user"
    ]),
    Character("Luke Skywalker", "Fiction", [
        "Star Wars hero", "Jedi knight", "Tatooine native", "X-wing pilot", "Son of Vader"
    ]),
    Character("Frodo Baggins", "Fiction", [
        "Hobbit", "Ring bearer", "Shire resident", "Mount Doom journey", "Samwise friend"
    ]),
    Character("Gandalf", "Fiction", [
        "Wizard", "Grey/White wizard", "Staff user", "You shall not pass", "Middle-earth guide"
    ]),
    Character("Batman", "Fiction", [
        "Superhero", "Bruce Wayne", "Gotham City", "No superpowers", "Rich orphan"
    ]),
    Character("Superman", "Fiction", [
        "Superhero", "Clark Kent", "Krypton origin", "Flying ability", "Weak to kryptonite"
    ]),
    Character("Spider-Man", "Fiction", [
        "Superhero", "Peter Parker", "Web shooter", "New York City", "Spider bite origin"
    ]),
    
    # Modern figures
    Character("Elon Musk", "Technology", [
        "Tesla CEO", "SpaceX founder", "South African-born", "Twitter owner", "Electric cars pioneer"
    ]),
    Character("Steve Jobs", "Technology", [
        "Apple co-founder", "iPhone creator", "Black turtleneck", "Pixar founder", "Think different"
    ]),
    Character("Bill Gates", "Technology", [
        "Microsoft co-founder", "Windows creator", "Philanthropist", "Harvard dropout", "Billionaire"
    ]),
    Character("Mark Zuckerberg", "Technology", [
        "Facebook founder", "Meta CEO", "Harvard student", "Social media pioneer", "Hoodie wearer"
    ]),
    
    # Entertainment
    Character("Michael Jackson", "Music", [
        "King of Pop", "Moonwalk dancer", "Thriller album", "Glove wearer", "Neverland Ranch"
    ]),
    Character("The Beatles", "Music", [
        "British band", "Liverpool origin", "John Paul George Ringo", "Abbey Road", "Let it be"
    ]),
    Character("Elvis Presley", "Music", [
        "King of Rock and Roll", "Graceland resident", "Jailhouse Rock", "Hawaii concert", "Leather jacket"
    ]),
    
    # More fictional
    Character("James Bond", "Fiction", [
        "British spy", "007 agent", "Martini drinker", "Aston Martin driver", "Shaken not stirred"
    ]),
    Character("Indiana Jones", "Fiction", [
        "Archaeologist", "Whip user", "Temple of Doom", "Hat wearer", "Snake hater"
    ]),
    Character("Pikachu", "Fiction", [
        "Pokémon", "Electric mouse", "Ash's partner", "Yellow creature", "Thunder attack"
    ]),
    Character("Mario", "Fiction", [
        "Video game character", "Plumber", "Nintendo mascot", "Mustache wearer", "Jumpman"
    ]),
    Character("Wonder Woman", "Fiction", [
        "Superhero", "Amazon princess", "Lasso of Truth", "Invisible jet", "Justice League member"
    ]),
]

def get_random_characters(count: int) -> List[Character]:
    """Get random unique characters from database"""
    return random.sample(CHARACTERS, min(count, len(CHARACTERS)))

def get_character_by_name(name: str) -> Character:
    """Find character by name (case-insensitive)"""
    for char in CHARACTERS:
        if char.name.lower() == name.lower():
            return char
    return None

def get_all_categories() -> List[str]:
    """Get all unique categories"""
    return list(set(char.category for char in CHARACTERS))

# Character validation
def validate_character_name(name: str) -> bool:
    """Check if character exists in database"""
    return get_character_by_name(name) is not None
