import csv
import sys
import logging

from util import Node, StackFrontier, QueueFrontier

# Maps names to a set of corresponding person_ids
names = {}

# Maps person_ids to a dictionary of: name, birth, movies (a set of movie_ids)
people = {}

# Maps movie_ids to a dictionary of: title, year, stars (a set of person_ids)
movies = {}

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def load_data(directory):
    """
    Load data from CSV files into memory.
    """
    # Load people
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set()
            }
            if row["name"].lower() not in names:
                names[row["name"].lower()] = {row["id"]}
            else:
                names[row["name"].lower()].add(row["id"])

    # Load movies
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set()
            }

    # Load stars
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                pass


def main():
    if len(sys.argv) > 2:
        sys.exit("Usage: python degrees.py [directory]")
    directory = sys.argv[1] if len(sys.argv) == 2 else "small"

    # Load data from files into memory
    print("Loading data...")
    load_data(directory)
    print("Data loaded.")

    source = person_id_for_name(input("Name: "))
    if source is None:
        sys.exit("Person not found.")
    target = person_id_for_name(input("Name: "))
    if target is None:
        sys.exit("Person not found.")

    path = shortest_path(source, target)

    if path is None:
        print("Not connected.")
    else:
        degrees = len(path)
        print(f"{degrees} degrees of separation.")
        path = [(None, source)] + path
        for i in range(degrees):
            person1 = people[path[i][1]]["name"]
            person2 = people[path[i + 1][1]]["name"]
            movie = movies[path[i + 1][0]]["title"]
            print(f"{i + 1}: {person1} and {person2} starred in {movie}")


def shortest_path(source, target):
    """
    @param source = the id of the source person 
    @param target = the id of the target person 

    Returns the shortest list of (movie_id, person_id) pairs
    that connect the source to the target.

    If no possible path, returns None.
    """

  # Initialise Frontier with source person_id as state
    logging.debug("Initializing the search with source person_id: %s", source)
    startingNode = Node(source, parent=None, action=None)
    frontier = StackFrontier()
    frontier.add(startingNode)

    # Track explored nodes
    exploredPeople = set()  # Using a hash table with unordered unique elements
    numExploredNodes = 0

    while True:
        # Check whether frontier is empty
        if frontier.empty():
            logging.error("No solution found, frontier is empty")
            raise Exception("No solution")

        # Remove node to explore
        node = frontier.remove()
        numExploredNodes += 1
        logging.debug("Exploring node with person_id: %s", node.state)

        exploredPeople.add(node.state)
        logging.debug("Added person_id %s to explored set", node.state)

        # Explore movies the actor starred in and look for co-actors
        moviesActorStarredIn = neighbors_for_person(node.state)
        logging.debug("Found %d co-actors for person_id %s", len(moviesActorStarredIn), node.state)

        for co_actor in moviesActorStarredIn:
            movieId = co_actor[0]
            personId = co_actor[1]

            logging.debug("Considering co-actor with person_id %s from movie_id %s", personId, movieId)

            if not frontier.contains_state(personId) and personId not in exploredPeople:
                logging.debug("Adding person_id %s to frontier", personId)
                # Check if it's the solution and return
                solution = checkForTargetPerson(personId, target, node)  # Assuming this function is defined elsewhere
                if solution is not None:
                    logging.info("Solution found: %s", solution)
                    return solution
                else:
                    child = Node(personId, node, movieId)
                    frontier.add(child)
                    logging.info(" Added Person with id %s and parent node %s and movie %s", personId, node, movieId)
    

def checkForTargetPerson(currentPersonId, targetId, node):
    logging.debug("Checking if current person_id %s is the target person_id %s", currentPersonId, targetId)
    
    if currentPersonId == targetId:
        logging.info("Target person_id %s found", targetId)
        
        movies = []
        people = []
        
        # Reconstruct the path from the target node to the source
        logging.debug("Reconstructing the path from target to source")
        while node.parent is not None:
            movies.append(node.action)
            people.append(node.state)
            logging.debug("Added movie_id %s and person_id %s to the path", node.action, node.state)
            node = node.parent
            
        movies.reverse()
        people.reverse()
        logging.debug("Path reconstruction completed. Movies: %s, People: %s", movies, people)
        
        solution = (movies, people)
        return solution
    
    else:
        logging.debug("Current person_id %s is not the target. Continuing search.", currentPersonId)
        return None




def person_id_for_name(name):
    """
    Returns the IMDB id for a person's name,
    resolving ambiguities as needed.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        return None
    elif len(person_ids) > 1:
        print(f"Which '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            name = person["name"]
            birth = person["birth"]
            print(f"ID: {person_id}, Name: {name}, Birth: {birth}")
        try:
            person_id = input("Intended Person ID: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


def neighbors_for_person(person_id):
    """
    Returns (movie_id, person_id) pairs for people
    who starred with a given person.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for person_id in movies[movie_id]["stars"]:
            neighbors.add((movie_id, person_id))
    return neighbors


if __name__ == "__main__":
    main()
