rule [
	labelType "term"
	left [
		edge [ source 10 target 1 label "-" ]
		edge [ source 3 target 12 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 3 label "Cl" ]
		node [ id 4 label "C" ]
		node [ id 10 label "N" ]
		node [ id 11 label "C" ]
		node [ id 12 label "H" ]
		node [ id 9 label "Cl" ]
		edge [ source 1 target 2 label "=" ]
		edge [ source 1 target 4 label "-" ]
		edge [ source 11 target 10 label "-" ]
		edge [ source 4 target 9 label "-" ]
	]
	right [
		edge [ source 3 target 1 label "-" ]
		edge [ source 10 target 12 label "-" ]
	]
]