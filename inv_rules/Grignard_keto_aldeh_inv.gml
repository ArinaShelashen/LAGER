rule [
	labelType "term"
	left [
		edge [ source 2 target 3 label "-" ]
		edge [ source 8 target 3 label "-" ]
		edge [ source 9 target 5 label "-" ]
		edge [ source 2 target 6 label "-" ]
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
		edge [ source 1 target 2 label "-" ]
		edge [ source 5 target 4 label "-" ]
		edge [ source 9 target 10 label "-" ]
		edge [ source 2 target 7 label "-" ]
	]
	right [
		edge [ source 6 target 5 label "-" ]
		edge [ source 2 target 3 label "=" ]
		edge [ source 8 target 9 label "-" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" label "N" label "S" ]
		edgeLabels [ label "=" label "#" ]
	]
	constrainLabelAny [ label "_X" labels [ label "Cl" label "Br" label "I" ] ]
	constrainLabelAny [ label "_Y" labels [ label "H" label "C" ] ]
	constrainLabelAny [ label "_Z" labels [ label "H" label "C" ] ]
]