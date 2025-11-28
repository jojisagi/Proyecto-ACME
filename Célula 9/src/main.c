/*
	Basado en el repositorio de raylib-quickstart, se ha modificado el archivo main.c 
	para que el logo rebote en las paredes de la ventana y se pueda controlar la velocidad del logo con un slider.
*/

// biblioteca de raylib
#include "raylib.h"
// biblioteca de funciones matemáticas de raylib
#include "raymath.h"
// biblioteca de funciones de recursos de raylib
#include "resource_dir.h"

int main ()
{
	// activar Vsync y escalar la ventana en pantallas de alta resolución
	SetConfigFlags(FLAG_VSYNC_HINT | FLAG_WINDOW_HIGHDPI);

	// Crear la ventana y contexto de OpenGL
	InitWindow(1280, 800, "Hello Raylib");

	// Establecer el directorio de recursos
	SearchAndSetResourceDir("resources");

	// Cargar una textura
	Texture logo = LoadTexture("logo.png");

	// posición inicial del logo
	Vector2 logoPosition = { GetScreenWidth()/2, GetScreenHeight()};
	float desiredWidth = 100;
	float desiredHeight = 100;
	Vector2 logoScale = { desiredWidth / logo.width, desiredHeight / logo.height };

	Vector2 velocity = { 1, -1 };
	printf("Screen Size: %i,%i\n", GetScreenWidth(),GetScreenHeight);

	//slider para controlar velocidad
	Rectangle sliderTrack = { GetScreenWidth() * 0.25f,
								GetScreenHeight() - 50,
								GetScreenWidth() * 0.5f,
								10 };
	float sliderRadius = 25;
	float sliderPosition = sliderTrack.x+100;
	bool sliderPressed = false;

	
	// game loop
	while (!WindowShouldClose())		// run the loop untill the user presses ESCAPE or presses the Close button on the window
	{
		//por convencion se calculan primero los inputs, osea, el slider
		if (IsMouseButtonDown(MOUSE_LEFT_BUTTON))
		{
			if (CheckCollisionPointCircle(GetMousePosition(), (Vector2){ sliderPosition, sliderTrack.y + sliderTrack.height / 2 }, sliderRadius))
			{
				sliderPressed = true;
				sliderPosition = GetMouseX();
				if (sliderPosition < sliderTrack.x)
					sliderPosition = sliderTrack.x;
				if (sliderPosition > sliderTrack.x + sliderTrack.width)
					sliderPosition = sliderTrack.x + sliderTrack.width;
			}
		}
		else
		{
			sliderPressed = false;
		}
		float speedScale = 1000 * ((sliderPosition - sliderTrack.x) / sliderTrack.width);
		//printf("Speed Scale: %f\n", speedScale);
		velocity = Vector2Normalize(velocity);
		velocity = Vector2Scale(velocity, speedScale);


		logoPosition.x += velocity.x * GetFrameTime();
		logoPosition.y += velocity.y * GetFrameTime();

		//rebotes
		if (logoPosition.x <= 0)
		{
			velocity.x *= -1;
			logoPosition.x = 0;
		}
		if (logoPosition.x >= GetScreenWidth() - logo.width)
		{
			velocity.x *= -1;
			logoPosition.x = GetScreenWidth() - logo.width;
		}
		if (logoPosition.y <= 0)
		{
			velocity.y *= -1;
			logoPosition.y = 0;
		}
		if(logoPosition.y >= GetScreenHeight() - logo.height)
		{
			velocity.y *= -1;
			logoPosition.y = GetScreenHeight() - logo.height;
		}


		// drawing
		BeginDrawing();

		// Limpiar la pantalla con un color gris
		ClearBackground(GRAY);

		// dibujar texto con la fuente predeterminada de raylib
		DrawText("Hello Raylib", 200,200,20,WHITE);

		// dibujar el logo en la posición calculada
		DrawTextureEx(logo, logoPosition, 0, logoScale.x, WHITE);

		//dibujar la barra de control de velocidad
		DrawRectangleRec(sliderTrack, DARKGRAY);
		DrawCircle(sliderPosition, sliderTrack.y + sliderTrack.height/2, sliderRadius, sliderPressed ? RED : MAROON);
		
		// terminar el dibujado
		EndDrawing();
	}

	// liberar la memoria de la textura
	UnloadTexture(logo);

	// destruir la ventana y liberar la memoria de los recursos de raylib
	CloseWindow();
	return 0;
}
