SELECT 
	* 
FROM 
	assignments 
INNER JOIN 
	roomies 
	USING(roomie_id) 
INNER JOIN 
	housework 
	USING(housework_id) 
ORDER BY 
	assignment_id 
ASC
;

