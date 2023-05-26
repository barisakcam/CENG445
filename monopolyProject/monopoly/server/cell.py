class Cell:

    def __init__(self, cell_info) -> None:
        self.type = cell_info["type"]
        self.number = cell_info["cell"]
        if self.type == "property":
            self.property = Property(cell_info, self.number)
    
    def __repr__(self) -> str:
        if self.type == "property":
            return "Cell:\n" + str(self.property)
        return "Cell:\n\t" + str(self.type)
    
    def get(self) -> dict:
        if self.type == "property":
            return self.property.get()
        else:
            return {"type": self.type, "number": self.number}

class Property:
    def __init__(self, cell_info, number):
        self.name = cell_info["name"]
        self.number = number
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
        return {"type": "property", \
                "name": self.name, \
                "number": self.number, \
                "color": self.color, \
                "price": self.price, \
                "rents": self.rents, \
                "owner": self.owner, \
                "level": self.level}
