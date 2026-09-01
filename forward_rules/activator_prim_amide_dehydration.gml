rule [
	labelType "term"
	left [
		edge [ source 7 target 8 label "-" ]
		edge [ source 2 target 6 label "-" ]
		edge [ source 10 target 2 label "-" ]
		edge [ source 5 target 1 label "=" ]
		edge [ source 1 target 2 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "N" ]
		node [ id 5 label "O" ]
		node [ id 7 label "2H" ]
		node [ id 8 label "O" ]
		node [ id 9 label "H" ]
		node [ id 6 label "H" ]
		node [ id 10 label "H" ]
		edge [ source 8 target 9 label "-" ]
	]
	right [
		edge [ source 10 target 8 label "-" ]
		edge [ source 7 target 5 label "-" ]
		edge [ source 6 target 5 label "-" ]
		edge [ source 1 target 2 label "#" ]
	]
]