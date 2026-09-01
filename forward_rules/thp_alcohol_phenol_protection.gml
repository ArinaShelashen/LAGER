rule [
	labelType "term"
	left [
		node [ id 11 label "O+" ]
		node [ id 9 label "H" ]
		edge [ source 6 target 5 label "=" ]
		edge [ source 11 target 10 label "-" ]
		edge [ source 7 target 9 label "-" ]
	]
	context [
		node [ id 1 label "O" ]
		node [ id 2 label "C" ]
		node [ id 3 label "C" ]
		node [ id 4 label "C" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "O" ]
		node [ id 8 label "C" ]
		node [ id 10 label "H" ]
		node [ id 12 label "H" ]
		node [ id 13 label "H" ]
		edge [ source 2 target 1 label "-" ]
		edge [ source 1 target 6 label "-" ]
		edge [ source 5 target 4 label "-" ]
		edge [ source 4 target 3 label "-" ]
		edge [ source 3 target 2 label "-" ]
		edge [ source 8 target 7 label "-" ]
		edge [ source 11 target 12 label "-" ]
		edge [ source 11 target 13 label "-" ]
	]
	right [
		node [ id 11 label "O" ]
		node [ id 9 label "H+" ]
		edge [ source 6 target 5 label "-" ]
		edge [ source 7 target 6 label "-" ]
		edge [ source 10 target 5 label "-" ]
	]
	constrainAdj [
		id 8
		op "="
		count 1
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 8
		op "="
		count 0
		nodeLabels [ label "N" label "P" label "S" label "F" label "Cl" label "I" label "Br" ]
	]
]