rule [
	labelType "term"
	left [
		node [ id 12 label "N" ]
		node [ id 22 label "C" ]
		edge [ source 22 target 23 label "=" ]
		edge [ source 12 target 2 label "-" ]
	]
	context [
		node [ id 23 label "O" ]
		node [ id 2 label "Br" ]
		node [ id 14 label "C" ]
		node [ id 15 label "O" ]
		node [ id 16 label "C" ]
		node [ id 17 label "O" ]
		node [ id 18 label "C" ]
		node [ id 19 label "C" ]
		edge [ source 12 target 14 label "-" ]
		edge [ source 14 target 15 label "=" ]
		edge [ source 12 target 16 label "-" ]
		edge [ source 16 target 17 label "=" ]
		edge [ source 14 target 18 label "-" ]
		edge [ source 18 target 19 label "-" ]
		edge [ source 19 target 16 label "-" ]
	]
	right [
		node [ id 12 label "N-" ]
		node [ id 22 label "C+" ]
		edge [ source 2 target 23 label "-" ]
		edge [ source 22 target 23 label "-" ]
	]
	constrainAdj [
		id 22
		op "="
		count 1
		nodeLabels [ label "H" ]
	]
]