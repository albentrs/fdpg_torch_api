SELECT DISTINCT t1.[UUID] 
FROM [DB_KDS_Person] t1 LEFT JOIN 
[DB_KDS_Fall_Diagnosen] t2 ON t2.[UUID] = t1.[UUID] 
WHERE [ICD10GMDiagnosecode] = 'I25.13'
