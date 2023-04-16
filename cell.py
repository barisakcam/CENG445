class Cell:

    def __init__(self, cell_info) -> None:
        self.type = cell_info["type"]
        if self.type == "property":
            self.property = Property(cell_info)
    
    def __repr__(self) -> str:
        if self.type == "property":
            return "Cell:\n" + str(self.property)
        return "Cell:\n\t" + str(self.type)
    
    def get(self) -> dict:
        if self.type == "property":
            return self.property.get()
        else:
            return {"type": self.type}

class Property:
    def __init__(self, cell_info):
        self.name = cell_info["name"]
        self.number = cell_info["cell"]
        self.color = cell_info["color"]
        self.price = cell_info["price"]
        self.rents = cell_info["rents"]
        self.owner = None
        self.level = 1

    def matching(self,property):
        return self.color == property.color
    
    def __str__(self):
        return "\tproperty:" + "\n\t\tname: " + str(self.name) + "\n\t\tnumber: " + str(self.number) + "\n\t\tcolor: " + str(self.color) + "\n\t\tprice: " + str(self.price) + "\n\t\trents: " + str(self.rents)
    
    def get(self) -> dict:
        return {"name": self.name, \
                "number": self.number, \
                "color": self.color, \
                "price": self.price, \
                "rents": self.rents, \
                "owner": self.owner, \
                "level": self.level}
    
#1. Chance card: Player picks and chance card and follow the card.
#2. Teleport: Player pays a travel fee and jumps to whichever cell s/he wants. Operation of the cell is followed.
#3. Jail: Player has to get a double on dice or pay a bailing amount. Otherwise s/he waits for the next round. S/he cannot get rent during this period.
#4. Goto Jail: Player jumps to the closest jail cell.
#5. Start: First cell of the board. There is only one start cell and player is payed a lapping salary when s/he passes over this cell.
#6. Tax: Player pays a fixed amount of tax per property s/he owns. """

