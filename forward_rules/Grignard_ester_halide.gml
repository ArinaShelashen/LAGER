rule [
	labelType "term"
	left [
		edge [ source 2 target 3 label "=" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 11 target 12 label "-" ]
		edge [ source 15 target 14 label "-" ]
		edge [ source 8 target 9 label "-" ]
		edge [ source 6 target 5 label "-" ]
	]
	context [
		node [ id 1 label "_Z" ]
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "_X" ]
		node [ id 5 label "Mg" ]
		node [ id 6 label "C" ]
		node [ id 7 label "_Y" ]
		node [ id 8 label "H" ]
		node [ id 9 label "O" ]
		node [ id 10 label "H" ]
		node [ id 11 label "Mg" ]
		node [ id 12 label "C" ]
		node [ id 13 label "_X" ]
		node [ id 14 label "H" ]
		node [ id 15 label "O" ]
		node [ id 16 label "H" ]
		edge [ source 5 target 4 label "-" ]
		edge [ source 9 target 10 label "-" ]
		edge [ source 2 target 7 label "-" ]
		edge [ source 16 target 15 label "-" ]
		edge [ source 13 target 11 label "-" ]
	]
	right [
		edge [ source 2 target 3 label "-" ]
		edge [ source 12 target 2 label "-" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 14 target 1 label "-" ]
		edge [ source 15 target 11 label "-" ]
		edge [ source 8 target 3 label "-" ]
		edge [ source 9 target 5 label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" label "N" label "S" ]
		edgeLabels [ label "=" label "#" ]
	]
	constrainAdj [
		id 12
		op "="
		count 0
		nodeLabels [ label "O" label "N" label "S" ]
		edgeLabels [ label "=" label "#" ]
	]
	constrainLabelAny [ label "_X" labels [ label "Cl" label "Br" label "I" ] ]
	constrainLabelAny [ label "_Y" labels [ label "H" label "C" ] ]
	constrainLabelAny [ label "_Z" labels [ label "O" label "Cl" label "Br" label "I" ] ]
]