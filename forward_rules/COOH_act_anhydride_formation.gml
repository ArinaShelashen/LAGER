rule [
	labelType "term"
	left [
		edge [ source 2 target 7 label "-" ]
		edge [ source 8 target 9 label "-" ]
	]
	context [
		node [ id 1 label "C" ]
		node [ id 2 label "O" ]
		node [ id 5 label "O" ]
		node [ id 7 label "2H" ]
		node [ id 8 label "C" ]
		node [ id 9 label "O" ]
		node [ id 10 label "H" ]
		node [ id 11 label "O" ]
		edge [ source 5 target 1 label "=" ]
		edge [ source 1 target 2 label "-" ]
		edge [ source 11 target 8 label "=" ]
		edge [ source 10 target 9 label "-" ]
	]
	right [
		edge [ source 8 target 2 label "-" ]
		edge [ source 9 target 7 label "-" ]
	]
]