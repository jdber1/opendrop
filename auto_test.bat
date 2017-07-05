@echo off
if "%1" == "pendantDrop" (
    python auto_test.py --pendantDrop 
    
    ) else (
        if "%1" == "sessileDrop" (
            python auto_test.py --sessileDrop 
        ) else (
            if "%1" == "contactAn" (
                python auto_test.py --contactAn 
            ) else (
                if "%1" == "contactAnNeedle" (
                    python auto_test.py --contactAnNeedle  
                ) else (
                    echo "wrong arguments for autotest"
                )
               
            )
        )
    )



