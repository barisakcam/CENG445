# CENG445
Online Monopoly


A Monopoly game is a board game with a simple cyclic array of cells. Each cell can be an property or
trigger an action. Each property has a buying price, upgrade price and 5 levels of rents. When a user
buys a property, s/he pays the buying price. When another user arrives the cell, s/he pays the rent for its
current level, initially 1. When the same user arrives the cell, s/he can pay upgrade price to increment to
level up to 5. Users start with an initial amount, earn rents from their properties and pay rent of others,
and buy properties on his/her budget.

The other types of cells are:
1. Chance card: Player picks and chance card and follow the card.
2. Teleport: Player pays a travel fee and jumps to whichever cell s/he wants. Operation of the cell is
followed.
3. Jail: Player has to get a double on dice or pay a bailing amount. Otherwise s/he waits for the next
round. S/he cannot get rent during this period.
4. Goto Jail: Player jumps to the closest jail cell.
5. Start: First cell of the board. There is only one start cell and player is payed a lapping salary when
s/he passes over this cell.
6. Tax: Player pays a fixed amount of tax per property s/he owns.

The type of chance cards are:
1. Upgrade: A property of users choice will be upgraded.
2. Downgrade: A property of users choice will be downgraded.
3. Color Upgrade: All properties of a color is upgraded. The users should own a property with same
color.
4. Color Downgrade: All properties of a color is upgraded. The users should own a property with same
color.
5. Goto Jail: User jumps to the closest jail cell.
6. Jail free: User stores this card and use it to go out of cell without pay.
4
7. Teleport: User jumps to any location s/he chooses without paying. Cells operation is executed (buy,
upgrade, chance etc).
8. Lottery: User wins lottery and gets the lottery amount.
9. Tax: User pays a fixed amount tax per property s/he owns.
A monopoly board is given as an input file in the following format:
{ cells: [{ type: "start"},
{ type: "property", name: 'bostancı', cell: 2, color: 'red',
price:120, rents: [50,150,400,600,900]},
{ type: "teleport"}, {type: "tax"}, {type: "jail},...]
upgrade: 50, teleport: 100, jailbail: 100,
tax: 30, lottery: 200, startup: 1500,
chances: [{type: "jump"},...}]
}
