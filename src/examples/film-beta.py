import datetime, os, sys, re, time

try:
    import imdb
except ImportError:
    imdb = None

from rdflib import BNode, ConjunctiveGraph, URIRef, Literal, Namespace, RDF
from rdflib.namespace import FOAF, DC

storefn = os.path.expanduser("~/movies.n3")
userfn = os.path.expanduser("~/users.n3")

storeuri = "file://" + storefn
useruri = "file://" + userfn

title_store = "Movie Theater managmented by %s"
title_user  = "Users"

r_who = re.compile(
    r"^(.*?) <([a-z0-9_-]+(\.[a-z0-9_-]+)*@[a-z0-9_-]+(\.[a-z0-9_-]+)+)>$"
)

IMDB = Namespace("http://www.csd.abdn.ac.uk/~ggrimnes/dev/imdb/IMDB#")
REV = Namespace("http://purl.org/stuff/rev#")

class Store:
    def __init__(self):
        self.graph = ConjunctiveGraph()
        if os.path.exists(storefn):
            self.graph.load(storeuri, format="n3")
        self.graph.bind("dc", DC)
        self.graph.bind("foaf", FOAF)
        self.graph.bind("imdb", IMDB)
        self.graph.bind("rev", "http://purl.org/stuff/rev#")

    def save(self):
        self.graph.serialize(storeuri, format="n3")

    def who(self, who=None):
        if who is not None:
            print("Welcome to the Store")
            name, email = (r_who.match(who).group(1), r_who.match(who).group(2))
            self.graph.add((URIRef(storeuri), DC["title"], Literal(title % name)))
            self.graph.add((URIRef(storeuri + "#author"), RDF.type, FOAF["Person"]))
            self.graph.add((URIRef(storeuri + "#author"), FOAF["name"], Literal(name)))
            self.graph.add((URIRef(storeuri + "#author"), FOAF["mbox"], Literal(email)))
            self.save()
        else:
            print("Your name is : ")
#            print(list(self.graph.objects(URIRef(storeuri + "#author"), FOAF["name"])))
            return self.graph.objects(URIRef(storeuri + "#author"), FOAF["name"])

    def new_movie(self, movie):
        movieuri = URIRef("https://www.imdb.com/title/tt%s/" % movie.movieID)
        self.graph.add((movieuri, RDF.type, IMDB["Movie"]))
        self.graph.add((movieuri, DC["title"], Literal(movie["title"])))
        self.graph.add((movieuri, IMDB["year"], Literal(int(movie["year"]))))
        self.save()

    def new_review(self, movie, date, rating, comment=None):
        review = BNode()  # @@ humanize the identifier (something like #rev-$date)
        movieuri = URIRef("https://www.imdb.com/title/tt%s/" % movie.movieID)
        self.graph.add((movieuri, REV["hasReview"], URIRef("%s#%s" % (storeuri, review))))
        self.graph.add((review, RDF.type, REV["Review"]))
        self.graph.add((review, DC["date"], Literal(date)))
        self.graph.add((review, REV["maxRating"], Literal(5)))
        self.graph.add((review, REV["minRating"], Literal(0)))
        self.graph.add((review, REV["reviewer"], URIRef(storeuri + "#author")))
        self.graph.add((review, REV["rating"], Literal(rating)))
        if comment is not None:
            self.graph.add((review, REV["text"], Literal(comment)))
        self.save()

    def __doc__(self):
        return False;

    def movie_is_in(self, uri):
        return (URIRef(uri), RDF.type, IMDB["Movie"]) in self.graph

    def help():
        print(__doc__.split("--")[1])


def main(argv=None):
    if not argv:
        argv = sys.argv
    s = Store()
    if argv[1] in ("help", "--help", "h", "-h"):
        help()
    elif argv[1] == "whoami":
        if os.path.exists(storefn):
            print(list(s.who())[0])
        else:
            s.who(argv[2])
    elif argv[1].startswith("https://www.imdb.com/title/tt"):
        if s.movie_is_in(argv[1]):
            raise Exception ("The movie has already been here")
        else:
            i = imdb.IMDb()
            movie = i.get_movie(argv[1][len("https://www.imdb.com/title/tt") : -1])
            print("%s (%s)" % (movie["title"].encode("utf-8"), movie["year"]))
            for director in movie["director"]:
                print("directed by: %s" % director["name"].encode("utf-8"))
            for writer in movie["writer"]:
                print("written by: %s" % writer["name"].encode("utf-8"))
            s.new_movie(movie) #Registrar la cabecera de la pelicula (nombre, fecha de revision, tipo de objeto)
            rating = None
            while not rating or (rating > 5 or rating <= 0):
                try:
                    rating = int(eval(input("Rating (on five): ")))
                except ValueError:
                    rating = None
            date = None
            while not date:
                try:
                    i = eval(input("Review date (YYYY-MM-DD): "))
                    date = datetime.datetime(*time.strptime(i, "%Y-%m-%d")[:6])
                except:
                    date = None
            comment = eval(input("Comment: "))
            s.new_review(movie, date, rating, comment) # Se regitra el detalle de la revision de la peicula
    else:
        help()


if __name__ == "__main__":
    if not imdb:
        raise Exception(
            'This example requires the IMDB library! Install with "pip install imdbpy"'
        )
    main()
