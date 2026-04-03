import random

# -------- DIALOGUE SYSTEM --------

dialogue = {
"cocky": [
"You really thought you had me there? That’s cute.",
"I don’t lose. I just let people think they had a chance.",
"All that confidence… for that hand?",
"You should’ve folded while you still had chips.",
"I’ve seen better bluffs from beginners.",
"This table? Yeah, it’s mine now.",
"Keep raising… you’re just digging deeper.",
"I don’t chase luck. Luck chases me.",
"Hope you brought more chips."
],

"serious": [
"Focus.",
"I’ve already read your play.",
"Your pattern is obvious.",
"This ends now.",
"You hesitate. That’s your weakness.",
"I don’t gamble. I calculate.",
"Every move you make… I’ve seen before.",
"You’re predictable.",
"No mistakes."
],

"funny": [
"Bro what are you DOING",
"Ain’t no way you just played that",
"You bluffing or just confused?",
"Did you mean to do that?",
"I respect the confidence… not the play though.",
"You got heart. No skill, but heart.",
"This isn’t UNO bro",
"You good? Need a tutorial?"
],

"straightup": [
"That was a bad move.",
"You’re overplaying your hand.",
"You should’ve folded.",
"That raise made no sense.",
"You’re chasing losses.",
"Think before you act.",
"That’s not how you win.",
"Play smarter."
],

"smart": [
"Your odds didn’t justify that.",
"You ignored the pot odds.",
"That bluff had no setup.",
"You misread the board.",
"Your range is weak here.",
"You’re telegraphing your moves.",
"That play was mathematically unsound."
],

"win": [
"And that’s game.",
"Too easy.",
"Told you.",
"You walked right into that.",
"That’s how it’s done.",
"Better luck next time.",
"I didn’t even try."
],

"lose": [
"Lucky.",
"That won’t happen again.",
"You got one. Don’t get comfortable.",
"Alright… now I’m locked in.",
"Enjoy it while it lasts.",
"Now it gets serious."
],

"casino": [
"The house always wins… let’s see if you can prove me wrong.",
"You’re in my territory now.",
"Every chip you lose belongs to me.",
"High stakes… high consequences.",
"Walk away while you still can.",
"This table breaks people."
]
}

# -------- FUNCTION TO GET RANDOM LINE --------

def get_dialogue(category):
    if category in dialogue:
        return random.choice(dialogue[category])
        return "..."

# -------- EXAMPLES --------

print("Cocky:", get_dialogue("cocky"))
print("Funny:", get_dialogue("funny"))
print("Serious:", get_dialogue("serious"))
print("Win:", get_dialogue("win"))
