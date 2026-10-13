#!/usr/bin/env python3
"""
Generates a realistic, rich Spotify Music Track dataset with controlled anomalies
for testing data validation, quarantine routing, MapReduce, Pig, Hive, and PySpark analytics.
"""

import csv
import random
import uuid
import os

SEED = 42
random.seed(SEED)

GENRES_ARTISTS = {
    "Rock": [
        ("Queen", ["Bohemian Rhapsody", "Don't Stop Me Now", "Under Pressure", "Radio Ga Ga", "Somebody to Love", "We Will Rock You", "Killer Queen"]),
        ("Pink Floyd", ["Comfortably Numb", "Wish You Were Here", "Time", "Money", "Another Brick in the Wall", "Shine On You Crazy Diamond"]),
        ("Led Zeppelin", ["Stairway to Heaven", "Whole Lotta Love", "Immigrant Song", "Black Dog", "Kashmir", "Ramble On"]),
        ("AC/DC", ["Back in Black", "Highway to Hell", "Thunderstruck", "T.N.T.", "Hells Bells", "Shoot to Thrill"]),
        ("The Rolling Stones", ["Paint It Black", "Sympathy for the Devil", "Gimme Shelter", "Satisfaction", "Angie", "Wild Horses"])
    ],
    "Pop": [
        ("Taylor Swift", ["Cruel Summer", "Blank Space", "Anti-Hero", "Shake It Off", "Love Story", "Style", "Cardigan", "Lover"]),
        ("The Weeknd", ["Blinding Lights", "Starboy", "Save Your Tears", "Can't Feel My Face", "The Hills", "Die for You", "After Hours"]),
        ("Dua Lipa", ["Levitating", "Don't Start Now", "Physical", "New Rules", "Dance The Night", "Houdini", "Break My Heart"]),
        ("Bruno Mars", ["Uptown Funk", "Locked Out of Heaven", "24K Magic", "Just the Way You Are", "Grenade", "Treasure"]),
        ("Ariana Grande", ["7 rings", "thank u next", "Positions", "Side to Side", "Into You", "No Tears Left to Cry"])
    ],
    "Hip-Hop": [
        ("Kendrick Lamar", ["HUMBLE.", "Alright", "DNA.", "King Kunta", "Swimming Pools", "Money Trees", "Not Like Us", "Family Ties"]),
        ("Drake", ["God's Plan", "One Dance", "Hotline Bling", "Passionfruit", "Hold On We're Going Home", "In My Feelings", "Nonstop"]),
        ("Eminem", ["Lose Yourself", "Without Me", "The Real Slim Shady", "Till I Collapse", "Stan", "Mockingbird", "Love The Way You Lie"]),
        ("Travis Scott", ["SICKO MODE", "Goosebumps", "Highest in the Room", "FE!N", "Antidote", "Butterfly Effect"]),
        ("J. Cole", ["No Role Modelz", "MIDDLE CHILD", "Wet Dreamz", "Power Trip", "ATM", "Deja Vu"])
    ],
    "Electronic": [
        ("Daft Punk", ["Get Lucky", "One More Time", "Around the World", "Harder Better Faster Stronger", "Instant Crush", "Digital Love"]),
        ("Avicii", ["Wake Me Up", "Levels", "The Nights", "Waiting For Love", "Hey Brother", "Without You"]),
        ("Calvin Harris", ["Summer", "Feel So Close", "One Kiss", "This Is What You Came For", "Outside", "How Deep Is Your Love"]),
        ("Deadmau5", ["Ghosts 'n' Stuff", "Strobe", "The Veldt", "Raise Your Weapon", "I Remember", "Some Chords"]),
        ("Kygo", ["Firestone", "Stole the Show", "It Ain't Me", "Higher Love", "Remind Me to Forget", "Stay"])
    ],
    "Jazz": [
        ("Miles Davis", ["So What", "Blue in Green", "Freddie Freeloader", "All Blues", "Flamenco Sketches", "Round Midnight"]),
        ("John Coltrane", ["Giant Steps", "A Love Supreme", "Naima", "My Favorite Things", "Blue Train", "Equinox"]),
        ("Bill Evans", ["Waltz for Debby", "Autumn Leaves", "Peace Piece", "My Foolish Heart", "Alice in Wonderland"]),
        ("Ella Fitzgerald", ["Dream a Little Dream of Me", "Cheek to Cheek", "Summertime", "Cry Me a River", "Lullaby of Birdland"]),
        ("Chet Baker", ["I Fall in Love Too Easily", "My Funny Valentine", "Born to Be Blue", "Almost Blue", "Time After Time"])
    ],
    "Classical": [
        ("Ludwig van Beethoven", ["Symphony No. 5", "Moonlight Sonata", "Fur Elise", "Symphony No. 9", "Pathetique Sonata"]),
        ("Wolfgang Amadeus Mozart", ["Eine kleine Nachtmusik", "Requiem in D minor", "The Magic Flute", "Piano Sonata No. 16", "Symphony No. 40"]),
        ("Johann Sebastian Bach", ["Toccata and Fugue in D minor", "Air on the G String", "Brandenburg Concerto No. 3", "Cello Suite No. 1"]),
        ("Frederic Chopin", ["Nocturne in E-flat major", "Fantaisie-Impromptu", "Ballade No. 1", "Waltz in C-sharp minor", "Prelude in E minor"]),
        ("Pyotr Ilyich Tchaikovsky", ["Swan Lake", "The Nutcracker", "1812 Overture", "Piano Concerto No. 1", "Sleeping Beauty"])
    ],
    "R&B": [
        ("SZA", ["Kill Bill", "Snooze", "Good Days", "Broken Clocks", "The Weekend", "Nobody Gets Me", "I Hate U"]),
        ("Frank Ocean", ["Thinkin Bout You", "Lost", "Pink + White", "Nights", "Novacane", "Ivy", "Chanel"]),
        ("Beyonce", ["Crazy in Love", "Halo", "CUFF IT", "Formation", "Love On Top", "Single Ladies", "Texas Hold 'Em"]),
        ("Usher", ["Yeah!", "My Boo", "Burn", "Confessions Part II", "DJ Got Us Fallin' In Love", "U Got It Bad"]),
        ("Alicia Keys", ["If I Ain't Got You", "No One", "Fallin'", "Empire State of Mind", "Girl on Fire", "You Don't Know My Name"])
    ],
    "Metal": [
        ("Metallica", ["Enter Sandman", "Master of Puppets", "Nothing Else Matters", "One", "Fade to Black", "For Whom the Bell Tolls"]),
        ("Iron Maiden", ["The Trooper", "Fear of the Dark", "Run to the Hills", "Hallowed Be Thy Name", "Aces High", "The Number of the Beast"]),
        ("Black Sabbath", ["Paranoid", "Iron Man", "War Pigs", "Children of the Grave", "Heaven and Hell", "N.I.B."]),
        ("Judas Priest", ["Breaking the Law", "Painkiller", "Living After Midnight", "Electric Eye", "You've Got Another Thing Comin'"]),
        ("Megadeth", ["Holy Wars", "Symphony of Destruction", "Peace Sells", "Tornado of Souls", "A Tout Le Monde"])
    ],
    "Country": [
        ("Johnny Cash", ["I Walk the Line", "Ring of Fire", "Folsom Prison Blues", "Hurt", "Man in Black", "Jackson"]),
        ("Dolly Parton", ["Jolene", "9 to 5", "I Will Always Love You", "Coat of Many Colors", "Here You Come Again"]),
        ("Luke Combs", ["Fast Car", "Beautiful Crazy", "She Got the Best of Me", "When It Rains It Pours", "Forever After All"]),
        ("Morgan Wallen", ["Last Night", "Whiskey Glasses", "Wasted on You", "Thought You Should Know", "Chasin' You"]),
        ("Chris Stapleton", ["Tennessee Whiskey", "You Should Probably Leave", "Broken Halos", "Starting Over", "Parachute"])
    ],
    "Indie": [
        ("Arctic Monkeys", ["Do I Wanna Know?", "505", "R U Mine?", "Why'd You Only Call Me When You're High?", "Fluorescent Adolescent", "I Wanna Be Yours"]),
        ("The Strokes", ["Last Nite", "Reptilia", "Someday", "The Adults Are Talking", "Hard to Explain", "You Only Live Once"]),
        ("Tame Impala", ["The Less I Know the Better", "Feels Like We Only Go Backwards", "Let It Happen", "Borderline", "Breathe Deeper"]),
        ("Vampire Weekend", ["A-Punk", "Campus", "Harmony Hall", "Oxford Comma", "Diane Young", "This Life"]),
        ("The Neighbourhood", ["Sweater Weather", "Daddy Issues", "Softcore", "Afraid", "Reflections"])
    ]
}

def generate_tracks(output_path, num_valid=5000, num_invalid=50):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    records = []
    
    # 1. Generate Valid Records
    genres = list(GENRES_ARTISTS.keys())
    for i in range(num_valid):
        genre = random.choice(genres)
        artist, titles = random.choice(GENRES_ARTISTS[genre])
        base_title = random.choice(titles)
        track_id = f"TRK{uuid.uuid4().hex[:12].upper()}"
        # Variation in titles for large dataset
        track_name = f"{base_title} (Live)" if random.random() < 0.1 else (f"{base_title} - Remix" if random.random() < 0.05 else base_title)
        album_name = f"{base_title} - The Collection" if random.random() < 0.3 else f"{artist} Masterworks"
        
        # Realistic popularity with genre-specific biases
        if genre in ["Pop", "Hip-Hop", "Indie"]:
            popularity = min(100, max(20, int(random.gauss(72, 14))))
        elif genre in ["Rock", "R&B"]:
            popularity = min(100, max(15, int(random.gauss(65, 15))))
        else:
            popularity = min(100, max(5, int(random.gauss(52, 18))))
            
        duration_ms = int(random.gauss(210000, 45000))
        duration_ms = max(60000, min(600000, duration_ms))
        
        explicit = 1 if genre in ["Hip-Hop", "R&B", "Metal"] and random.random() < 0.4 else (1 if random.random() < 0.1 else 0)
        year = random.randint(1965, 2024)
        
        records.append({
            "track_id": track_id,
            "track_name": track_name,
            "artist_name": artist,
            "album_name": album_name,
            "genre": genre,
            "popularity": popularity,
            "duration_ms": duration_ms,
            "explicit": explicit,
            "year": year
        })
    
    # 2. Inject Controlled Invalid Records for Quarantine & Data Quality Testing
    invalid_cases = [
        # (type, track_id, track_name, artist, album, genre, pop, duration, explicit, year)
        ("NEGATIVE_DURATION", "TRK_ERR_001", "Broken Duration Track", "Error Artist", "Fault Album", "Rock", 50, -120000, 0, 2021),
        ("ZERO_DURATION", "TRK_ERR_002", "Zero Duration Track", "Error Artist", "Fault Album", "Pop", 60, 0, 0, 2022),
        ("POPULARITY_OVER_MAX", "TRK_ERR_003", "Hyper Popular Track", "Error Artist", "Fault Album", "Hip-Hop", 150, 180000, 0, 2020),
        ("POPULARITY_NEGATIVE", "TRK_ERR_004", "Negative Popularity", "Error Artist", "Fault Album", "Indie", -10, 200000, 0, 2019),
        ("MISSING_TRACK_NAME", "TRK_ERR_005", "", "Error Artist", "Fault Album", "Electronic", 45, 210000, 0, 2023),
        ("MISSING_ARTIST_NAME", "TRK_ERR_006", "Ghost Track", "", "Fault Album", "Jazz", 40, 240000, 0, 2018),
        ("MISSING_GENRE", "TRK_ERR_007", "No Genre Track", "Error Artist", "Fault Album", "", 55, 195000, 0, 2021),
        ("INVALID_EXPLICIT_VALUE", "TRK_ERR_008", "Bad Explicit Flag", "Error Artist", "Fault Album", "Rock", 62, 220000, 99, 2020),
        ("YEAR_OUT_OF_BOUNDS", "TRK_ERR_009", "Time Traveler Track", "Error Artist", "Fault Album", "Country", 70, 210000, 0, 2099),
        ("TOO_SHORT_DURATION", "TRK_ERR_010", "Subsecond Glitch", "Error Artist", "Fault Album", "Classical", 30, 250, 0, 2022)
    ]
    
    # Repeat invalid cases to reach requested invalid count
    while len(invalid_cases) < num_invalid:
        idx = len(invalid_cases) + 1
        case_type = random.choice(["NEGATIVE_DURATION", "POP_OVER", "NULL_NAME", "BAD_YEAR"])
        if case_type == "NEGATIVE_DURATION":
            invalid_cases.append(("NEGATIVE_DURATION", f"TRK_ERR_{idx:03d}", f"Corrupt Audio {idx}", "Glitch Band", "Error", "Rock", 40, -50000, 0, 2020))
        elif case_type == "POP_OVER":
            invalid_cases.append(("POP_OVER", f"TRK_ERR_{idx:03d}", f"Fake Hype {idx}", "Viral Bot", "Hype", "Pop", 250, 150000, 0, 2024))
        elif case_type == "NULL_NAME":
            invalid_cases.append(("NULL_NAME", f"TRK_ERR_{idx:03d}", "", "Anonymous", "Unknown", "Indie", 20, 180000, 0, 2015))
        else:
            invalid_cases.append(("BAD_YEAR", f"TRK_ERR_{idx:03d}", f"Ancient Track {idx}", "Historian", "Vault", "Classical", 15, 300000, 0, 1820))

    for item in invalid_cases[:num_invalid]:
        records.append({
            "track_id": item[1],
            "track_name": item[2],
            "artist_name": item[3],
            "album_name": item[4],
            "genre": item[5],
            "popularity": item[6],
            "duration_ms": item[7],
            "explicit": item[8],
            "year": item[9]
        })
        
    # Also inject 10 duplicate records to test duplicate handling
    for d in range(10):
        dup_source = records[d].copy()
        records.append(dup_source)
        
    random.shuffle(records)
    
    fieldnames = [
        "track_id", "track_name", "artist_name", "album_name", 
        "genre", "popularity", "duration_ms", "explicit", "year"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    print(f"Generated {len(records)} records ({num_valid} valid, {num_invalid} synthetic invalid anomalies, 10 duplicate pairs) to {output_path}")

if __name__ == "__main__":
    generate_tracks("data/sample/music_tracks.csv", num_valid=5000, num_invalid=50)
